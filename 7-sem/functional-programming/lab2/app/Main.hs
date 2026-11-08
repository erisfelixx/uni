{-# LANGUAGE BangPatterns #-}


-- Розв'язання системи лінійних рівнянь паралельним методом Гаусса.
-- Компіляція з ключем -threaded (див. gauss.cabal), запуск: cabal run або напряму: ghc -O2 -threaded -rtsopts app/Main.hs -o gauss ./gauss +RTS -N4
--
-- Ідея паралелізму:
--   на k-му кроці прямого ходу рядки k+1..n-1 віднімають від себе ведучий рядок k НЕЗАЛЕЖНО один від одного. 
--   Тому їх ділимо на неперервні блоки, і кожен блок обробляє окремий потік (forkOn — потік на окремому ядрі).
--   Головний потік чекає завершення всіх (MVar) — бар'єр між кроками.
--   Гонок даних немає: кожен потік пише лише у свої рядки, а ведучий рядок k на цьому кроці тільки читається.
-- =====================================================================
module Main (main) where

import Control.Concurrent (MVar, forkOn, getNumCapabilities, newEmptyMVar, putMVar, takeMVar)
import Control.Exception (Exception, SomeException, displayException, evaluate, mask, throwIO, try)
import Control.Monad (foldM, forM, forM_, replicateM, when)
import Data.Array.Base (unsafeRead, unsafeWrite)
import Data.Array.IO (IOUArray, getElems, newArray, newListArray)
import Data.Bits (shiftR)
import Data.List (intercalate, nub, transpose)
import Data.Word (Word64)
import GHC.Clock (getMonotonicTime)
import GHC.Conc (getNumProcessors)
import System.Directory (createDirectoryIfMissing)
import System.FilePath (takeDirectory)
import System.IO
import System.Mem (performMajorGC)
import Text.Printf (printf)
import Text.Read (readMaybe)



-- 1. Типи даних

-- | Система A·x = b у "чистому" вигляді (списки) — для введення, генерації та перевірки розв'язку.
data LinearSystem = LinearSystem
  { lsA :: [[Double]]
  , lsB :: [Double]
  }

-- | Розширена матриця [A | b] розміром n × (n+1) для обчислень.
-- Зберігається рядками в одному змінюваному НЕупакованому масиві
-- (IOUArray Int Double): швидкий доступ, без "лінивих" значень.
data Matrix = Matrix !Int !(IOUArray Int Double)

-- | Налаштування паралельного алгоритму.
data Config = Config
  { cfgThreads   :: !Int    -- максимальна кількість потоків
  , cfgMinWork   :: !Int    -- мінімум елементів на один потік (гранулярність)
  , cfgVerbose   :: !Bool   -- покрокове виведення (для малих систем)
  , cfgForceFork :: !Bool   -- створювати потоки навіть для одного блоку
  }

-- | Послідовна версія: без створення потоків, усе в головному потоці.
seqConfig :: Config
seqConfig = Config 1 0 False False

-- | Паралельна версія з t потоками (потоки створюються завжди,
-- тож "паралельна на 1 потоці" включає витрати на їх створення).
parConfig :: Int -> Int -> Config
parConfig t minWork = Config t minWork False True

-- | Виняток: матриця вироджена (немає єдиного розв'язку).
newtype SingularMatrix = SingularMatrix Int

instance Show SingularMatrix where
  show (SingularMatrix k) =
    "Матриця вироджена: на кроці " ++ show (k + 1)
      ++ " усі можливі ведучі елементи дорівнюють нулю"

instance Exception SingularMatrix

-- | Поріг, нижче якого число вважається нулем.
eps :: Double
eps = 1e-12

-- | Гранулярність за замовчуванням: потоку варто давати хоча б ~4096 елементів роботи, інакше витрати на створення потоку більші за виграш.
defaultMinWork :: Int
defaultMinWork = 4096

-- | Індекс елемента (i, j) у плоскому масиві.
idx :: Int -> Int -> Int -> Int
idx n i j = i * (n + 1) + j
{-# INLINE idx #-}

-- | Цикл for i in [lo, hi) без створення проміжних списків.
loop :: Int -> Int -> (Int -> IO ()) -> IO ()
loop lo hi body = go lo
  where
    go !i
      | i >= hi = return ()
      | otherwise = body i >> go (i + 1)
{-# INLINE loop #-}



-- 2. Паралельний цикл (fork-join)

-- | Ділить діапазон [lo, hi) на t майже рівних неперервних блоків.
chunks :: Int -> Int -> Int -> [(Int, Int)]
chunks t lo hi = [(lo + bound i, lo + bound (i + 1)) | i <- [0 .. t - 1]]
  where
    cnt = hi - lo
    bound i = (i * cnt) `div` t

-- | Номер ядра (capability), на якому працює потік з номером th (0, 1, ...).
-- Потоки розподіляються по ядрах по колу.
capabilityFor :: Int -> Int -> Int
capabilityFor caps th = th `mod` max 1 caps

-- | Паралельний for: кожен блок діапазону виконує окремий потік.
--   forkOn  — запускає потік на заданому ядрі (capability), тож блоки гарантовано обчислюються на різних ядрах;
--   try     — потік перехоплює свою помилку і передає її головному;
--   MVar    — кожен потік кладе в свою MVar результат завершення, головний потік чекає всі MVar (бар'єр синхронізації).
-- mask/restore гарантують, що потік повідомить про завершення навіть у разі асинхронного винятку.
-- force = False: один блок виконується прямо в головному потоці.

parallelFor :: Bool -> Int -> Int -> Int -> (Int -> IO ()) -> IO ()
parallelFor force threads lo hi body
  | hi <= lo = return ()
  | threads <= 1 && not force = loop lo hi body
  | otherwise = do
      caps <- getNumCapabilities
      dones <- forM (zip [0 ..] (chunks threads lo hi)) $ \(th, (a, b)) -> do
        done <- newEmptyMVar :: IO (MVar (Either SomeException ()))
        _ <- mask $ \restore ->
               forkOn (capabilityFor caps th) (try (restore (loop a b body)) >>= putMVar done)
        return done
      forM_ dones $ \d -> takeMVar d >>= either throwIO return

-- | Скільки потоків доцільно задіяти на кроці з rows рядками по cols елементів: не більше заданих, не більше рядків і не менше cfgMinWork елементів на потік.
threadsFor :: Config -> Int -> Int -> Int
threadsFor cfg rows cols
  | rows <= 0 = 1
  | otherwise = max 1 (minimum [cfgThreads cfg, rows, (rows * cols) `div` max 1 (cfgMinWork cfg)])



-- 3. Метод Гаусса

-- | Створює розширену матрицю з чистого представлення системи.
newMatrix :: LinearSystem -> IO Matrix
newMatrix (LinearSystem a b) =
  Matrix n <$> newListArray (0, n * (n + 1) - 1) (concat (zipWith (\row bi -> row ++ [bi]) a b))
  where
    n = length b

-- | Міняє місцями рядки r1 і r2.
swapRows :: Matrix -> Int -> Int -> IO ()
swapRows (Matrix n a) r1 r2 = loop 0 (n + 1) $ \j -> do
  x <- unsafeRead a (idx n r1 j)
  y <- unsafeRead a (idx n r2 j)
  unsafeWrite a (idx n r1 j) y
  unsafeWrite a (idx n r2 j) x

-- | Вибір ведучого елемента в стовпці k (частковий вибір): рядок з найбільшим |a[i][k]|, i >= k. Підвищує точність.
pivotRow :: Matrix -> Int -> IO Int
pivotRow (Matrix n a) k = foldM better k [k + 1 .. n - 1]
  where
    better best i = do
      v  <- abs <$> unsafeRead a (idx n i k)
      bv <- abs <$> unsafeRead a (idx n best k)
      return (if v > bv then i else best)

-- | Виключення змінної x_k з рядка i: рядок_i -= f · рядок_k, де f = a[i][k] / a[k][k]. Саме ця операція виконується паралельно.
eliminateRow :: Matrix -> Int -> Double -> Int -> IO ()
eliminateRow (Matrix n a) k pivot i = do
  aik <- unsafeRead a (idx n i k)
  when (aik /= 0) $ do
    let f = aik / pivot
    unsafeWrite a (idx n i k) 0
    loop (k + 1) (n + 1) $ \j -> do
      akj <- unsafeRead a (idx n k j)
      aij <- unsafeRead a (idx n i j)
      unsafeWrite a (idx n i j) (aij - f * akj)

-- | Прямий хід: зведення матриці до верхньотрикутного вигляду.
-- Кроки k виконуються послідовно (кожен залежить від попереднього), а рядки всередині кроку — паралельно.
forwardElimination :: Config -> Matrix -> IO ()
forwardElimination cfg m@(Matrix n a) = loop 0 n $ \k -> do
  p <- pivotRow m k
  when (p /= k) (swapRows m k p)
  pivot <- unsafeRead a (idx n k k)
  when (abs pivot < eps) (throwIO (SingularMatrix k))

  let rows = n - 1 - k
      t = threadsFor cfg rows (n + 1 - k)

  when (cfgVerbose cfg && rows > 0) $ do
    caps <- getNumCapabilities
    printf "\nКрок %d: ведучий елемент a[%d][%d] = %.4f" (k + 1) (k + 1) (k + 1) pivot
    when (p /= k) (printf " (переставлено рядки %d і %d)" (k + 1) (p + 1))
    putStrLn ""
    forM_ (zip [0 :: Int ..] (chunks t (k + 1) n)) $ \(th, (lo, hi)) -> do
      let core = if t <= 1 && not (cfgForceFork cfg)
                   then "головний потік"
                   else "ядро " ++ show (capabilityFor caps th)
      if hi - lo == 1
        then printf "  потік %d (%s): рядок %d\n" (th + 1) core hi
        else printf "  потік %d (%s): рядки %d–%d\n" (th + 1) core (lo + 1) hi

  parallelFor (cfgForceFork cfg) t (k + 1) n (eliminateRow m k pivot)

  when (cfgVerbose cfg && rows > 0) (printMatrix m)

-- | Зворотний хід: x_i = (b_i - Σ_{j>i} a_ij·x_j) / a_ii, від останнього рядка.
-- Виконується послідовно: x_i залежить від усіх x_j, j > i.
-- Його складність O(n²) проти O(n³) прямого ходу.
backSubstitution :: Matrix -> IO [Double]
backSubstitution (Matrix n a) = do
  x <- newArray (0, n - 1) 0 :: IO (IOUArray Int Double)
  forM_ [n - 1, n - 2 .. 0] $ \i -> do
    s <- foldM (\ !acc j -> do
                  aij <- unsafeRead a (idx n i j)
                  xj  <- unsafeRead x j
                  return (acc + aij * xj))
               0 [i + 1 .. n - 1]
    bi  <- unsafeRead a (idx n i n)
    aii <- unsafeRead a (idx n i i)
    unsafeWrite x i ((bi - s) / aii)
  getElems x

-- | Повне розв'язання: прямий + зворотний хід.
solveMatrix :: Config -> Matrix -> IO [Double]
solveMatrix cfg m = forwardElimination cfg m >> backSubstitution m



-- 4. Перевірка, генерація, виведення (чисті функції)

-- | Нев'язка ||A·x - b|| (максимум модуля): наскільки x задовольняє систему.
residual :: LinearSystem -> [Double] -> Double
residual (LinearSystem a b) x =
  maximum (0 : zipWith (\row bi -> abs (sum (zipWith (*) row x) - bi)) a b)

-- | Максимальна різниця між двома векторами.
maxDiff :: [Double] -> [Double] -> Double
maxDiff xs ys = maximum (0 : zipWith (\p q -> abs (p - q)) xs ys)

-- | Лінійний конгруентний генератор псевдовипадкових чисел.
lcg :: Word64 -> Word64
lcg s = s * 6364136223846793005 + 1442695040888963407

-- | Нескінченний лінивий список псевдовипадкових чисел у [-1, 1).
uniforms :: Word64 -> [Double]
uniforms = map toUnit . drop 1 . iterate lcg
  where
    toUnit s = fromIntegral (s `shiftR` 11) / 9007199254740992 * 2 - 1

-- | Розбиває список на шматки довжини k.
chunkList :: Int -> [a] -> [[a]]
chunkList _ [] = []
chunkList k ys = take k ys : chunkList k (drop k ys)

-- | Випадкова система розміру n з відомим розв'язком x*, b = A·x*.
--   dominant = True  — діагональ підсилено (+n): матриця з діагональною перевагою, гарантовано невироджена;
--   dominant = False — довільна випадкова матриця (для тестів).
randomSystem :: Bool -> Int -> Word64 -> (LinearSystem, [Double])
randomSystem dominant n seed = (LinearSystem a b, xTrue)
  where
    (xs, rest) = splitAt n (uniforms seed)
    xTrue = map (* 10) xs
    boost = if dominant then fromIntegral n else 0
    a = [ [if i == j then v + boost else v | (j, v) <- zip [0 :: Int ..] row]
        | (i, row) <- zip [0 :: Int ..] (chunkList n (take (n * n) rest)) ]
    b = [sum (zipWith (*) row xTrue) | row <- a]

-- | Нескінченний список псевдовипадкових цілих у [lo, hi].
randomInts :: Int -> Int -> Word64 -> [Int]
randomInts lo hi seed =
  [lo + min (hi - lo) (floor ((u + 1) / 2 * fromIntegral (hi - lo + 1))) | u <- uniforms seed]

-- | Друк розширеної матриці.
printMatrix :: Matrix -> IO ()
printMatrix (Matrix n a) = forM_ [0 .. n - 1] $ \i -> do
  row <- mapM (\j -> unsafeRead a (idx n i j)) [0 .. n]
  putStrLn ("   " ++ concatMap (printf "%10.4f") (take n row)
            ++ "  |" ++ concatMap (printf "%10.4f") (drop n row))

-- | Друк розв'язку (для великих систем — лише перші 10 значень).
printSolution :: [Double] -> IO ()
printSolution xs = do
  putStrLn "\nРозв'язок:"
  forM_ (take 10 (zip [1 :: Int ..] xs)) $ \(i, v) -> printf "   x%-3d = %14.8f\n" i v
  when (length xs > 10) (printf "   ... (усього %d значень)\n" (length xs))



-- 5. Введення даних

prompt :: String -> IO String
prompt msg = putStr msg >> hFlush stdout >> getLine

-- | Ціле число в діапазоні; Enter — значення за замовчуванням.
askInt :: String -> Int -> Int -> Maybe Int -> IO Int
askInt lbl lo hi def = do
  s <- prompt (lbl ++ maybe "" (\d -> " [" ++ show d ++ "]") def ++ ": ")
  case (words s, def) of
    ([], Just d) -> return d
    _ -> case readMaybe s of
      Just v | v >= lo && v <= hi -> return v
      _ -> printf "  ! Введіть ціле число від %d до %d\n" lo hi >> askInt lbl lo hi def

-- | Розбір рядка чисел (дозволена кома як десятковий роздільник).
parseRow :: String -> Maybe [Double]
parseRow = mapM readNum . words . map (\c -> if c == ',' then '.' else c)
  where
    -- ".5" не розбирається read, тому пробуємо ще "0.5"
    readNum s = maybe (readMaybe ("0" ++ s)) Just (readMaybe s)

-- | Перевіряє, що рядки мають n+1 чисел, і будує систему.
buildSystem :: Int -> [[Double]] -> Either String LinearSystem
buildSystem n rows
  | length rows /= n = Left ("Очікувалось " ++ show n ++ " рядків, отримано " ++ show (length rows))
  | any ((/= n + 1) . length) rows = Left ("Кожен рядок має містити " ++ show (n + 1) ++ " чисел: a1 .. an b")
  | otherwise = Right (LinearSystem (map (take n) rows) (map last rows))

-- | Введення системи з клавіатури.
readFromKeyboard :: IO LinearSystem
readFromKeyboard = do
  n <- askInt "Кількість рівнянь n" 1 20 Nothing
  printf "Вводьте %d рядків по %d чисел: a1 a2 ... a%d b\n" n (n + 1) n
  rows <- forM [1 .. n] (readRow n)
  either (\e -> putStrLn ("  ! " ++ e) >> readFromKeyboard) return (buildSystem n rows)
  where
    readRow n i = do
      s <- prompt ("  рівняння " ++ show i ++ ": ")
      case parseRow s of
        Just r | length r == n + 1 -> return r
        _ -> printf "  ! Потрібно %d чисел\n" (n + 1) >> readRow n i

-- | Завантаження системи з файлу.
-- Формат: перший рядок — n, далі n рядків по n+1 чисел (a1 .. an b).
readFromFile :: IO LinearSystem
readFromFile = do
  path <- prompt "Шлях до файлу [data/example.txt]: "
  let file = if null (words path) then "data/example.txt" else path
  content <- readFile file
  case filter (not . null . words) (lines content) of
    (first : rest)
      | Just n <- readMaybe first, Just rows <- mapM parseRow rest ->
          either (\e -> throwIO (userError e)) return (buildSystem n rows)
    _ -> throwIO (userError "Неправильний формат файлу")



-- 6. Режими роботи


-- | Збереження розв'язку у текстовий файл.
saveSolution :: [Double] -> IO ()
saveSolution x = do
  s <- prompt "Зберегти розв'язок у файл? Шлях [Enter — не зберігати]: "
  case words s of
    [] -> return ()
    (path : _) -> do
      writeFile path (unlines [printf "x%d = %.10f" i v | (i, v) <- zip [1 :: Int ..] x])
      putStrLn ("Розв'язок збережено у " ++ path)

-- | Розв'язує систему, виводить розв'язок, час і перевірку, пропонує зберегти розв'язок у файл.
solveAndReport :: Int -> LinearSystem -> IO ()
solveAndReport caps sys = do
  let n = length (lsB sys)
      verbose = n <= 6
      cfg = Config caps (if verbose then 0 else defaultMinWork) verbose False
  m <- newMatrix sys
  when verbose (putStrLn "\nПочаткова розширена матриця [A | b]:" >> printMatrix m)
  t0 <- getMonotonicTime
  x <- solveMatrix cfg m
  _ <- evaluate (sum x)
  t1 <- getMonotonicTime
  printSolution x
  printf "\nПеревірка: нев'язка ||A·x - b|| = %.3e\n" (residual sys x)
  printf "Час розв'язання: %.6f с (до %d потоків)\n" (t1 - t0) caps
  saveSolution x

-- | Демонстраційна система 4×4, розв'язок (1, -1, 2, 1).
demoSystem :: LinearSystem
demoSystem = LinearSystem
  [ [ 2,  1, -1,  3]
  , [ 4, -6,  0,  1]
  , [-2,  7,  2, -1]
  , [ 1,  1,  5,  2] ]
  [2, 11, -6, 12]

-- | Система з data/example.txt, розв'язок (1, 2, 3, 4, 5).
example5 :: LinearSystem
example5 = LinearSystem
  [ [10,  2, -1,  3,  1]
  , [ 3, 12,  2, -1,  4]
  , [-2,  1,  9,  2, -3]
  , [ 1, -3,  2, 11,  2]
  , [ 4,  2, -1,  1, 15] ]
  [28, 49, 20, 55, 84]

-- | Система з нулем на діагоналі (a11 = 0): без перестановки рядків метод Гаусса тут ділив би на нуль. Розв'язок (1, 2, 3).
zeroDiag :: LinearSystem
zeroDiag = LinearSystem
  [ [0, 2, 1]
  , [1, 1, 1]
  , [2, 1, 0] ]
  [7, 6, 4]

-- | Демонстраційний приклад 4×4 з покроковим виведенням.
demo :: Int -> IO ()
demo caps = do
  putStrLn "\nСистема:"
  putStrLn "   2x1 +  x2 -  x3 + 3x4 =  2"
  putStrLn "   4x1 - 6x2        + x4 = 11"
  putStrLn "  -2x1 + 7x2 + 2x3 -  x4 = -6"
  putStrLn "    x1 +  x2 + 5x3 + 2x4 = 12"
  putStrLn "Очікуваний розв'язок: (1, -1, 2, 1)"
  solveAndReport caps demoSystem



-- 7. Вимірювання швидкодії

-- | Вимірює час розв'язання: runs запусків, повертає (середній час, мінімальний час, розв'язок).
-- Перед кожним запуском — повне прибирання сміття (performMajorGC), щоб воно не потрапляло в замір.
measure :: Int -> Config -> LinearSystem -> IO (Double, Double, [Double])
measure runs cfg sys = do
  (t, x) <- once
  rest <- replicateM (runs - 1) once
  let ts = t : map fst rest
  return (sum ts / fromIntegral (length ts), minimum ts, x)
  where
    once = do
      m <- newMatrix sys
      performMajorGC
      t0 <- getMonotonicTime
      sol <- solveMatrix cfg m
      _ <- evaluate (sum sol)
      t1 <- getMonotonicTime
      return (t1 - t0, sol)

-- | Таблиця для консолі.
renderTable :: [String] -> [[String]] -> String
renderTable hdr rows = unlines (fmt hdr : sep : map fmt rows)
  where
    widths = map (maximum . map length) (transpose (hdr : rows))
    fmt r = intercalate "  " [c ++ replicate (w - length c) ' ' | (c, w) <- zip r widths]
    sep = intercalate "  " [replicate w '-' | w <- widths]

markdownTable :: [String] -> [[String]] -> String
markdownTable hdr rows = unlines (row hdr : row (map (const "---") hdr) : map row rows)
  where
    row cs = "| " ++ intercalate " | " cs ++ " |"

-- | Порівняння послідовної версії та паралельної на 1, 2, 4, ... потоках.
benchmark :: Int -> Int -> IO ()
benchmark procs caps = do
  n    <- askInt "Розмір системи n" 2 2000 (Just 1000)
  runs <- askInt "Кількість запусків кожної конфігурації" 1 50 (Just 5)
  putStrLn "Генерація системи..."
  let (sys, xTrue) = randomSystem True n 2026
  _ <- evaluate (sum (map sum (lsA sys)) + sum (lsB sys))
  let threadCounts = nub (takeWhile (<= caps) (iterate (* 2) 1) ++ [caps])
  printf "Вимірювання: %d запусків на конфігурацію...\n\n" runs

  (seqMean, seqMin, xSeq) <- measure runs seqConfig sys
  par <- forM threadCounts $ \t -> do
    (mean, mn, x) <- measure runs (parConfig t defaultMinWork) sys
    return (t, mean, mn, x)

  let par1 = case par of
        ((_, mean, _, _) : _) -> mean
        [] -> seqMean
      f2 = printf "%.2f" :: Double -> String
      f4 = printf "%.4f" :: Double -> String
      hdr = [ "Версія", "Потоків", "Сер. час, с", "Мін. час, с"
            , "Приск. відн. 1 потоку", "Приск. відн. послідовної"
            , "Ефективність", "Відх. від послідовної" ]
      seqRow = ["послідовна", "1", f4 seqMean, f4 seqMin, "—", "1.00", "—", "0"]
      parRows =
        [ [ "паралельна", show t, f4 mean, f4 mn
          , f2 (par1 / mean), f2 (seqMean / mean)
          , f2 (par1 / mean / fromIntegral t)
          , printf "%.1e" (maxDiff x xSeq) ]
        | (t, mean, mn, x) <- par ]
      rows = seqRow : parRows
      speedups = [par1 / mean | (_, mean, _, _) <- par]
      err = maxDiff xSeq xTrue
      res = residual sys xSeq

  putStr (renderTable hdr rows)
  putStrLn "\nПрискорення рахується за середнім часом:"
  putStrLn "  відн. 1 потоку = T(паралельна, 1) / T(паралельна, p);"
  putStrLn "  відн. послідовної = T(послідовна) / T(паралельна, p);"
  putStrLn "  ефективність = прискорення відн. 1 потоку / p."
  printf "Похибка ||x - x*|| = %.3e,  нев'язка ||A·x - b|| = %.3e\n" err res

  -- Звіт у Markdown: таблиця + графік прискорення.
  let chart = unlines
        [ "```mermaid"
        , "xychart-beta"
        , "    title \"Прискорення паралельного методу Гаусса, n = " ++ show n ++ "\""
        , "    x-axis \"Потоки\" [" ++ intercalate ", " (map show threadCounts) ++ "]"
        , "    y-axis \"Прискорення\" 0 --> " ++ show (maximum threadCounts + 1)
        , "    bar [" ++ intercalate ", " (map f2 speedups) ++ "]"
        , "    line [" ++ intercalate ", " (map show threadCounts) ++ "]"
        , "```" ]
      report = unlines
        [ "# Вимірювання швидкодії"
        , ""
        , "Система " ++ show n ++ "×" ++ show n ++ " (випадкова, з діагональною перевагою), "
            ++ show runs ++ " запусків на конфігурацію."
        , "Ядер процесора: " ++ show procs ++ ", capabilities (+RTS -N): " ++ show caps ++ "."
        , ""
        , markdownTable hdr rows
        , "Стовпці — виміряне прискорення відносно 1 потоку, лінія — ідеальне."
        , ""
        , chart
        , printf "Похибка ||x − x*|| = %.3e, нев'язка ||A·x − b|| = %.3e." err res ]

  s <- prompt "\nЗберегти звіт (Markdown з таблицею і графіком)? Шлях [results/benchmark.md], '-' — ні: "
  case words s of
    ["-"] -> return ()
    ws -> do
      let path = case ws of
            [] -> "results/benchmark.md"
            (p : _) -> p
      createDirectoryIfMissing True (takeDirectory path)
      writeFile path report
      putStrLn ("Звіт збережено у " ++ path)



-- 8. Автоматичні тести

-- | Група тестів: назва, кількість перевірок, список невдач.
data TestResult = TestResult String Int [String]

-- | Розв'язання без винятку: Left — матриця вироджена.
solveWith :: Config -> LinearSystem -> IO (Either SingularMatrix [Double])
solveWith cfg sys = try (newMatrix sys >>= solveMatrix cfg)

-- | Конфігурація для тестів: гранулярність 0, тож потоки створюються навіть для малих систем і паралельний код справді виконується.
testConfig :: Int -> Config
testConfig t = parConfig t 0

-- | Перевірка: розв'язок відрізняється від очікуваного не більше ніж на tol.
expectSolution :: String -> Double -> Config -> LinearSystem -> [Double] -> IO [String]
expectSolution name tol cfg sys expected = do
  r <- solveWith cfg sys
  return $ case r of
    Left e -> [name ++ ": " ++ show e]
    Right x
      | maxDiff x expected <= tol -> []
      | otherwise -> [printf "%s: відхилення %.3e > %.0e" name (maxDiff x expected) tol]

-- | Виконує групу перевірок і збирає невдачі.
testGroup :: String -> [IO [String]] -> IO TestResult
testGroup name checks = TestResult name (length checks) . concat <$> sequence checks

-- | Замінює i-й елемент списку.
setAt :: Int -> a -> [a] -> [a]
setAt i v xs = take i xs ++ [v] ++ drop (i + 1) xs

-- | Норма матриці (максимальна сума модулів у рядку) і вектора.
normA :: [[Double]] -> Double
normA a = maximum (0 : map (sum . map abs) a)

normV :: [Double] -> Double
normV = maximum . (0 :) . map abs

-- | Усі групи тестів. Випадкові дані детерміновані (фіксовані seed), тож результат тестів відтворюваний.
allTests :: Int -> [IO TestResult]
allTests caps =
  [ testGroup "Відомі приклади (4×4, 5×5, нуль на діагоналі)"
      [ expectSolution "демо 4×4" 1e-9 (testConfig caps) demoSystem [1, -1, 2, 1]
      , expectSolution "файл 5×5" 1e-9 (testConfig caps) example5 [1, 2, 3, 4, 5]
      , expectSolution "a11 = 0" 1e-9 (testConfig caps) zeroDiag [1, 2, 3] ]

  , testGroup "Випадкові системи з діагональною перевагою, n = 1..80"
      [ do let (sys, xt) = randomSystem True n (fromIntegral i)
           expectSolution ("n=" ++ show n ++ ", seed " ++ show i) 1e-8 (testConfig 4) sys xt
      | (i, n) <- zip [1 :: Int .. 200] (randomInts 1 80 7) ]

  , testGroup "Довільні випадкові матриці: мала відносна нев'язка"
      [ do let (sys, _) = randomSystem False n (fromIntegral (1000 + i))
           r <- solveWith (testConfig 4) sys
           return $ case r of
             Left e -> ["n=" ++ show n ++ ": " ++ show e]
             Right x ->
               let rel = residual sys x / (normA (lsA sys) * normV x + normV (lsB sys))
               in [printf "n=%d: відносна нев'язка %.2e" n rel | rel > 1e-12 * fromIntegral n]
      | (i, n) <- zip [1 :: Int .. 100] (randomInts 2 60 11) ]

  , testGroup "Паралельний результат = послідовний (1, 2, 3, 4, 7 потоків)"
      [ do let (sys, _) = randomSystem True n (fromIntegral (2000 + i))
           base <- solveWith seqConfig sys
           others <- mapM (\t -> solveWith (testConfig t) sys) threadSet
           return [ printf "n=%d: результат на %d потоках відрізняється" n t
                  | (t, r) <- zip threadSet others, not (sameResult base r) ]
      | (i, n) <- zip [1 :: Int .. 100] (randomInts 1 80 13) ]

  , testGroup "Перестановка рядків (рядки системи переставлено)"
      [ do let (LinearSystem a b, xt) = randomSystem True n (fromIntegral (3000 + i))
               sys = LinearSystem (rotate a) (rotate b)
           expectSolution ("n=" ++ show n) 1e-8 (testConfig 4) sys xt
      | (i, n) <- zip [1 :: Int .. 50] (randomInts 2 40 17) ]

  , testGroup "Вироджені матриці розпізнаються"
      [ do let (LinearSystem a b, _) = randomSystem True n (fromIntegral (4000 + i))
               (r, s) = (i `mod` n, (i + 1) `mod` n)
               singular
                 | even i    = LinearSystem (setAt r (map (* 2) (a !! s)) a) b  -- рядок r = 2 · рядок s
                 | otherwise = LinearSystem (map (setAt r 0) a) b               -- нульовий стовпець r
           res <- solveWith (testConfig 4) singular
           return ["n=" ++ show n ++ ": вироджену матрицю не розпізнано" | isRight res]
      | (i, n) <- zip [1 :: Int .. 60] (randomInts 2 20 19) ]

  , testGroup "Граничні випадки"
      [ expectSolution "n = 1" 1e-12 (testConfig 4) (LinearSystem [[5]] [10]) [2]
      , expectSolution "потоків (16) більше, ніж рядків (3)" 1e-9 (testConfig 16) zeroDiag [1, 2, 3]
      , expectSolution "одинична матриця 50×50" 0 (testConfig 4) identity50 [1 .. 50] ]
  ]
  where
    threadSet = [1, 2, 3, 4, 7] :: [Int]
    rotate xs = drop 1 xs ++ take 1 xs
    isRight = either (const False) (const True)
    sameResult (Right x) (Right y) = maxDiff x y == 0
    sameResult (Left _) (Left _) = True
    sameResult _ _ = False
    identity50 = LinearSystem
      [[if i == j then 1 else 0 | j <- [1 .. 50 :: Int]] | i <- [1 .. 50 :: Int]]
      [1 .. 50]

-- | Запуск усіх тестів і підсумок.
runTests :: Int -> IO ()
runTests caps = do
  putStrLn "\nАвтоматичні тести (паралельний код виконується навіть на малих системах):\n"
  rs <- forM (allTests caps) $ \t -> do
    r@(TestResult name cnt fails) <- t
    if null fails
      then printf "  [OK]   %s — %d перевірок\n" name cnt
      else do
        printf "  [FAIL] %s — невдалих %d з %d\n" name (length fails) cnt
        mapM_ (putStrLn . ("         " ++)) (take 5 fails)
    return r
  let passed = length [() | TestResult _ _ [] <- rs]
      total  = sum [cnt | TestResult _ cnt _ <- rs]
  printf "\nПройдено груп тестів: %d з %d (усього перевірок: %d)\n" passed (length rs) total



-- 9. Головне меню

main :: IO ()
main = do
  hSetEncoding stdout utf8
  hSetEncoding stdin utf8
  hSetBuffering stdout NoBuffering
  caps  <- getNumCapabilities
  procs <- getNumProcessors
  putStrLn "=== Паралельний метод Гаусса (Haskell, -threaded) ==="
  printf "Ядер процесора: %d, потоків runtime (capabilities, +RTS -N): %d\n" procs caps
  menu procs caps

menu :: Int -> Int -> IO ()
menu procs caps = do
  putStrLn ""
  putStrLn "1. Демонстраційний приклад 4×4 (покроково)"
  putStrLn "2. Ввести систему з клавіатури"
  putStrLn "3. Завантажити систему з файлу"
  putStrLn "4. Порівняти швидкодію: послідовна і паралельна на 1..N потоках"
  putStrLn "5. Автоматичні тести"
  putStrLn "0. Вихід"
  choice <- prompt "> "
  case words choice of
    ["0"] -> putStrLn "До побачення!"
    ["1"] -> safely (demo caps) >> again
    ["2"] -> safely (readFromKeyboard >>= solveAndReport caps) >> again
    ["3"] -> safely (readFromFile >>= solveAndReport caps) >> again
    ["4"] -> safely (benchmark procs caps) >> again
    ["5"] -> safely (runTests caps) >> again
    _ -> putStrLn "  ! Невірний пункт меню" >> again
  where
    again = menu procs caps

-- | Виконує дію, перехоплюючи помилки (вироджена матриця, відсутній файл).
safely :: IO () -> IO ()
safely act = do
  r <- try act
  case r of
    Right () -> return ()
    Left e -> putStrLn ("  ! Помилка: " ++ displayException (e :: SomeException))