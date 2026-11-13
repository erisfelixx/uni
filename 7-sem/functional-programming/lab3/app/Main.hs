
-- Обробка тексту підручника з програмування на Haskell з використанням типів:
-- Символ, Слово, Речення (пропозиція),Розділовий знак, Елемент тексту, Текст.

-- Загальна вимога: табуляції та послідовності пробілів замінюються одним пробілом.
-- Варіант 15: перетворити кожне слово, видаливши з нього
--   (А) наступні входження ПЕРШОЇ літери слова;
--   (Б) попередні входження ОСТАННЬОЇ літери слова.
-- Літери порівнюються без урахування регістру ("Мама" -> "Маа").
--
-- Запуск: cabal run                    (файл data/textbook.txt)
--         cabal run lab3 -- шлях.txt   (інший файл)
-- =====================================================================
module Main (main) where

import Prelude hiding (Word)

import Control.Exception (SomeException, displayException, try)
import Control.Monad (forM_)
import Data.Char (isAlphaNum, isLetter, isSpace, toLower)
import Data.List (intercalate, nub, transpose)
import System.Directory (createDirectoryIfMissing, doesFileExist)
import System.Environment (getArgs)
import System.FilePath (takeDirectory)
import System.IO
import Text.Printf (printf)


-- 1. Типи даних

-- | Символ тексту.
newtype Symbol = Symbol Char
  deriving (Eq, Show)

-- | Слово: послідовність символів-літер, цифр або '_' (апостроф і дефіс допускаються лише всередині: пов’язаний, лямбда-числення).
newtype Word = Word [Symbol]
  deriving (Eq, Show)

-- | Розділовий знак: будь-який символ, що не є частиною слова чи пробілом
-- (. , ; : ! ? ( ) [ ] « » - + = тощо).
newtype Punctuation = Punctuation Symbol
  deriving (Eq, Show)

-- | Елемент речення.
data Token
  = TWord Word            -- слово
  | TPunct Punctuation    -- розділовий знак
  | TSpace                -- пробіл (замість будь-якої послідовності пробілів і табуляцій)
  | TNewline              -- кінець рядка
  deriving (Eq, Show)

-- | Речення (пропозиція): послідовність елементів, що закінчується знаком . ! ? або …
newtype Sentence = Sentence [Token]
  deriving (Eq, Show)

-- | Текст: послідовність речень.
newtype Text = Text [Sentence]
  deriving (Eq, Show)

-- | Режим перетворення за варіантом 15.
data Mode
  = FirstLetter   -- (А) видалити наступні входження першої літери
  | LastLetter    -- (Б) видалити попередні входження останньої літери
  deriving (Eq, Show)



-- 2. Класи типів та їх втілення

-- | Перетворення елемента тексту назад у рядок.
class Render a where
  render :: a -> String

instance Render Symbol where
  render (Symbol c) = [c]

instance Render Word where
  render (Word syms) = concatMap render syms

instance Render Punctuation where
  render (Punctuation s) = render s

instance Render Token where
  render (TWord w)  = render w
  render (TPunct p) = render p
  render TSpace     = " "
  render TNewline   = "\n"

instance Render Sentence where
  render (Sentence ts) = concatMap render ts

instance Render Text where
  render (Text ss) = concatMap render ss

-- | Структура, що містить слова: можна отримати всі слова і застосувати функцію до кожного слова, не змінюючи решти.
class HasWords a where
  wordsOf  :: a -> [Word]
  mapWords :: (Word -> Word) -> a -> a

instance HasWords Token where
  wordsOf (TWord w) = [w]
  wordsOf _         = []
  mapWords f (TWord w) = TWord (f w)
  mapWords _ t         = t

instance HasWords Sentence where
  wordsOf (Sentence ts) = concatMap wordsOf ts
  mapWords f (Sentence ts) = Sentence (map (mapWords f) ts)

instance HasWords Text where
  wordsOf (Text ss) = concatMap wordsOf ss
  mapWords f (Text ss) = Text (map (mapWords f) ss)



-- 3. Розбір тексту: String -> [Token] -> [Sentence] -> Text

-- | Пробільний символ у межах рядка (пробіл, табуляція тощо, крім переходу на новий рядок).
isBlank :: Char -> Bool
isBlank c = isSpace c && c /= '\n' && c /= '\r'

-- | Символ, з якого може складатися слово.
isWordChar :: Char -> Bool
isWordChar c = isAlphaNum c || c == '_'

-- | Апостроф або дефіс — допустимі лише всередині слова.
isJoiner :: Char -> Bool
isJoiner c = c `elem` "'’ʼ-"

-- | Розбиває рядок на елементи. Послідовність пробілів і табуляцій стає одним TSpace — саме тут виконується загальна вимога завдання.
tokenize :: String -> [Token]
tokenize [] = []
tokenize s@(c : cs)
  | c == '\r'    = tokenize cs
  | c == '\n'    = TNewline : tokenize cs
  | isBlank c    = TSpace : tokenize (dropWhile isBlank cs)
  | isWordChar c = let (w, rest) = spanWord s
                   in TWord (Word (map Symbol w)) : tokenize rest
  | otherwise    = TPunct (Punctuation (Symbol c)) : tokenize cs

-- | Виділяє слово з початку рядка. Апостроф/дефіс входять у слово, лише якщо за ними знову йде символ слова.
spanWord :: String -> (String, String)
spanWord (c : cs)
  | isWordChar c = let (w, rest) = spanWord cs in (c : w, rest)
spanWord (j : d : cs)
  | isJoiner j && isWordChar d = let (w, rest) = spanWord (d : cs) in (j : w, rest)
spanWord cs = ([], cs)

-- | Знак кінця речення.
isTerminal :: Token -> Bool
isTerminal (TPunct (Punctuation (Symbol c))) = c `elem` ".!?…"
isTerminal _ = False

-- | Знаки, що можуть стояти одразу після кінця речення (?!, ..., .»  .) ).
isClosing :: Token -> Bool
isClosing (TPunct (Punctuation (Symbol c))) = c `elem` ".!?…)»\"'"
isClosing _ = False

-- | Речення закінчується, якщо після знака кінця не йде одразу слово (так "3.14", "2.1" і "[1..10]" не розриваються).
endsHere :: [Token] -> Bool
endsHere (TWord _ : _) = False
endsHere _ = True

-- | Відокремлює перше речення від решти елементів.
takeSentence :: [Token] -> ([Token], [Token])
takeSentence [] = ([], [])
takeSentence (t : ts)
  | isTerminal t, (closing, rest) <- span isClosing ts, endsHere rest = (t : closing, rest)
  | otherwise = let (s, rest) = takeSentence ts in (t : s, rest)

-- | Ділить послідовність елементів на речення.
splitSentences :: [Token] -> [Sentence]
splitSentences [] = []
splitSentences ts = Sentence s : splitSentences rest
  where
    (s, rest) = takeSentence ts

-- | Повний розбір тексту.
parseText :: String -> Text
parseText = Text . splitSentences . tokenize

-- | Еталонна нормалізація пробілів без розбору (для перевірки в тестах).
normalizeSpaces :: String -> String
normalizeSpaces = go . filter (/= '\r')
  where
    go [] = []
    go (c : cs)
      | isBlank c = ' ' : go (dropWhile isBlank cs)
      | otherwise = c : go cs



-- 4. Перетворення за варіантом 15

-- | Чи є символ літерою (апостроф ʼ формально теж "літера" в Unicode, тому виключаємо його).
isLetterSym :: Symbol -> Bool
isLetterSym (Symbol c) = isLetter c && not (isJoiner c)

-- | Чи є символ s тією ж літерою, що й l (без урахування регістру).
sameLetter :: Symbol -> Symbol -> Bool
sameLetter (Symbol l) s@(Symbol c) = isLetterSym s && toLower c == toLower l

-- | Перетворення одного слова.
--   FirstLetter: знаходимо першу літеру; усі її НАСТУПНІ входження видаляємо.
--   LastLetter:  знаходимо останню літеру; усі її ПОПЕРЕДНІ входження видаляємо.
-- Слово без літер (наприклад, число) не змінюється.
transformWord :: Mode -> Word -> Word
transformWord FirstLetter (Word syms) =
  case break isLetterSym syms of
    (before, l : after) -> Word (before ++ l : filter (not . sameLetter l) after)
    _ -> Word syms
transformWord LastLetter (Word syms) =
  case break isLetterSym (reverse syms) of
    (afterRev, l : beforeRev) ->
      Word (reverse (filter (not . sameLetter l) beforeRev) ++ l : reverse afterRev)
    _ -> Word syms

-- | Перетворення всього тексту: змінюються лише слова, розділові знаки, пробіли й рядки залишаються на місці.
transformText :: Mode -> Text -> Text
transformText mode = mapWords (transformWord mode)

modeTitle :: Mode -> String
modeTitle FirstLetter = "(А) видалення наступних входжень ПЕРШОЇ літери слова"
modeTitle LastLetter  = "(Б) видалення попередніх входжень ОСТАННЬОЇ літери слова"

modeFile :: Mode -> FilePath
modeFile FirstLetter = "results/output_first_letter.txt"
modeFile LastLetter  = "results/output_last_letter.txt"



-- 5. Статистика та опис структури

-- | Усі елементи тексту.
tokensOf :: Text -> [Token]
tokensOf (Text ss) = concat [ts | Sentence ts <- ss]

-- | Кількість речень, що містять хоча б одне слово.
sentenceCount :: Text -> Int
sentenceCount (Text ss) = length [() | s <- ss, not (null (wordsOf s))]

-- | Опис елемента для демонстрації структури.
describe :: Token -> String
describe (TWord w)  = "Слово «" ++ render w ++ "»"
describe (TPunct p) = "Розділовий знак «" ++ render p ++ "»"
describe TSpace     = "Пробіл"
describe TNewline   = "Кінець рядка"

-- | Рядок без переходів на новий рядок (для короткого показу).
oneLine :: String -> String
oneLine = map (\c -> if c == '\n' then ' ' else c)



-- 6. Введення-виведення

readUtf8 :: FilePath -> IO String
readUtf8 path = withFile path ReadMode $ \h -> hSetEncoding h utf8 >> hGetContents' h

writeUtf8 :: FilePath -> String -> IO ()
writeUtf8 path s = do
  createDirectoryIfMissing True (takeDirectory path)
  withFile path WriteMode $ \h -> hSetEncoding h utf8 >> hPutStr h s

prompt :: String -> IO String
prompt msg = putStr msg >> hFlush stdout >> getLine

-- | Таблиця з вирівняними стовпцями.
printTable :: [String] -> [[String]] -> IO ()
printTable hdr rows
  | null rows = putStrLn "  (немає)"
  | otherwise = mapM_ (putStrLn . ("  " ++) . fmt) (hdr : sep : rows)
  where
    widths = [maximum (map length col) | col <- transpose (hdr : rows)]
    sep = [replicate w '-' | w <- widths]
    fmt r = intercalate "  " [c ++ replicate (w - length c) ' ' | (c, w) <- zip r widths]



-- 7. Режими роботи

-- | Пункт 1: нормалізований текст (без перетворення слів).
showNormalized :: Text -> IO ()
showNormalized txt = do
  putStrLn "\n=== Текст після заміни табуляцій і послідовностей пробілів одним пробілом ===\n"
  putStrLn (render txt)
  writeUtf8 "results/normalized.txt" (render txt)
  putStrLn "\nЗбережено у results/normalized.txt"

-- | Пункти 2 і 3: перетворення тексту за варіантом.
runTransform :: Mode -> Text -> IO ()
runTransform mode txt = do
  let result  = transformText mode txt
      pairs   = zip (wordsOf txt) (wordsOf result)
      changed = [(render a, render b) | (a, b) <- pairs, a /= b]
  printf "\n=== Перетворення %s ===\n\n" (modeTitle mode)
  putStrLn (render result)
  printf "\nСлів у тексті: %d, змінено: %d\n" (length pairs) (length changed)
  putStrLn "Приклади змін:"
  printTable ["Було", "Стало"] [[a, b] | (a, b) <- take 15 (nub changed)]
  writeUtf8 (modeFile mode) (render result)
  printf "Результат збережено у %s\n" (modeFile mode)

-- | Пункт 4: перетворення слів, введених з клавіатури.
transformInput :: IO ()
transformInput = do
  s <- prompt "Введіть слово або кілька слів: "
  let ws = wordsOf (parseText s)
  if null ws
    then putStrLn "  ! Слів не знайдено"
    else printTable ["Слово", "(А) перша літера", "(Б) остання літера"]
           [ [render w, render (transformWord FirstLetter w), render (transformWord LastLetter w)]
           | w <- ws ]

-- | Пункт 5: статистика і розбір структури перших речень.
showStructure :: Text -> IO ()
showStructure txt@(Text ss) = do
  let ts = tokensOf txt
      punct = [p | TPunct p <- ts]
  putStrLn "\n=== Структура тексту ==="
  printf "  Символів:          %d\n" (length (render txt))
  printf "  Рядків:            %d\n" (1 + length [() | TNewline <- ts])
  printf "  Речень:            %d\n" (sentenceCount txt)
  printf "  Слів:              %d\n" (length (wordsOf txt))
  printf "  Розділових знаків: %d\n" (length punct)
  printf "  Різних розділових знаків: %s\n" (unwords (nub (map render punct)))
  putStrLn "\nРозбір перших двох речень на елементи (без пробілів):"
  forM_ (zip [1 :: Int ..] (take 2 [s | s <- ss, not (null (wordsOf s))])) $ \(i, s@(Sentence sts)) -> do
    printf "\n  Речення %d: «%s»\n" i (oneLine (dropWhile isSpace (render s)))
    forM_ [t | t <- sts, t /= TSpace, t /= TNewline] $ \t -> putStrLn ("    " ++ describe t)



-- 8. Автоматичні тести

-- | Перевірка: назва та результат.
data Check = Check String Bool

-- | Очікувані результати для окремих слів: слово, режим (А), режим (Б).
wordCases :: [(String, String, String)]
wordCases =
  [ ("level",           "leve",           "evel")
  , ("programming",     "programming",    "proramming")
  , ("Мама",            "Маа",            "Мма")
  , ("аба",             "аб",             "ба")
  , ("Ааа",             "А",              "а")
  , ("лямбда-числення", "лямбда-чисення", "лмбда-числення")
  , ("з'являється",     "з'являється",    "з'влється")
  , ("Haskell98",       "Haskell98",      "Haskel98")
  , ("x",               "x",              "x")
  , ("2026",            "2026",           "2026") ]

-- | Перетворення рядка-слова (через розбір).
transformString :: Mode -> String -> String
transformString mode = render . transformText mode . parseText

-- | Кількість входжень літери l у слові.
countLetter :: Symbol -> Word -> Int
countLetter l (Word syms) = length (filter (sameLetter l) syms)

-- | Перша й остання літери слова.
firstLetter, lastLetter :: Word -> Maybe Symbol
firstLetter (Word syms) = case filter isLetterSym syms of
  (l : _) -> Just l
  [] -> Nothing
lastLetter (Word syms) = firstLetter (Word (reverse syms))

-- | Елементи тексту, крім слів (мають залишатися незмінними).
skeleton :: Text -> [Token]
skeleton txt = [t | t <- tokensOf txt, null (wordsOf t)]

-- | Усі перевірки: модульні (на прикладах) і властивості (на всьому файлі).
allChecks :: String -> Text -> [Check]
allChecks raw txt =
  -- окремі слова, обидва режими
  [ Check (printf "(А) %s -> %s" w a) (transformString FirstLetter w == a) | (w, a, _) <- wordCases ] ++
  [ Check (printf "(Б) %s -> %s" w b) (transformString LastLetter w == b) | (w, _, b) <- wordCases ] ++
  -- розбір і нормалізація
  [ Check "табуляції та пробіли -> один пробіл"
      (render (parseText "a\t\tb   c \t d") == "a b c d")
  , Check "3 речення: «Перше речення. Друге? Третє!»"
      (sentenceCount (parseText "Перше речення. Друге? Третє!") == 3)
  , Check "число 3.14 і номер 2.1 не розривають речення"
      (sentenceCount (parseText "Розділ 2.1 містить число 3.14 тут.") == 1)
  , Check "«Так... Ні?!» — 2 речення"
      (sentenceCount (parseText "Так... Ні?!") == 2)
  , Check "слова з апострофом і дефісом, код x+1, символ 'a'"
      (map render (wordsOf (parseText "лямбда-числення, пов’язаний 'a' x+1"))
         == ["лямбда-числення", "пов’язаний", "a", "x", "1"])
  , Check "дужка після крапки: «Як у Lisp.) Далі текст.» — 2 речення"
      (sentenceCount (parseText "Як у Lisp.) Далі текст.") == 2) ] ++
  -- властивості на тексті з файлу
  [ Check "файл: розбір + відображення = нормалізація пробілів"
      (render txt == normalizeSpaces raw)
  , Check "файл: у результаті немає табуляцій і подвійних пробілів"
      (let r = render txt in '\t' `notElem` r && not (hasDoubleSpace r))
  , Check "файл (А): після перетворення перша літера трапляється в слові 1 раз"
      (all (\w -> maybe True (\l -> countLetter l w == 1) (firstLetter w))
           (wordsOf (transformText FirstLetter txt)))
  , Check "файл (Б): після перетворення остання літера трапляється в слові 1 раз"
      (all (\w -> maybe True (\l -> countLetter l w == 1) (lastLetter w))
           (wordsOf (transformText LastLetter txt)))
  , Check "файл: повторне перетворення нічого не змінює (А і Б)"
      (and [transformText m (transformText m txt) == transformText m txt | m <- [FirstLetter, LastLetter]])
  , Check "файл: розділові знаки, пробіли й рядки не змінюються"
      (and [skeleton (transformText m txt) == skeleton txt | m <- [FirstLetter, LastLetter]])
  , Check "файл: кількість слів і речень не змінюється"
      (and [ length (wordsOf (transformText m txt)) == length (wordsOf txt)
             && sentenceCount (transformText m txt) == sentenceCount txt
           | m <- [FirstLetter, LastLetter] ]) ]
  where
    hasDoubleSpace (' ' : ' ' : _) = True
    hasDoubleSpace (_ : rest) = hasDoubleSpace rest
    hasDoubleSpace [] = False

-- | Пункт 6: запуск тестів.
runTests :: String -> Text -> IO ()
runTests raw txt = do
  putStrLn "\n=== Автоматичні тести ===\n"
  let checks = allChecks raw txt
  forM_ checks $ \(Check name ok) ->
    putStrLn ((if ok then "  [OK]   " else "  [FAIL] ") ++ name)
  let passed = length [() | Check _ True <- checks]
  printf "\nПройдено: %d з %d\n" passed (length checks)



-- 9. Головне меню

main :: IO ()
main = do
  hSetEncoding stdout utf8
  hSetEncoding stdin utf8
  hSetBuffering stdout NoBuffering
  putStrLn "=== Обробка тексту підручника з програмування (варіант 15) ==="
  args <- getArgs
  path <- case args of
    (p : _) -> return p
    [] -> askPath
  session path

-- | Запит шляху до файлу.
askPath :: IO FilePath
askPath = do
  s <- prompt "Файл з текстом [data/textbook.txt]: "
  return (if null (words s) then "data/textbook.txt" else s)

-- | Завантаження файлу і робота з ним.
session :: FilePath -> IO ()
session path = do
  exists <- doesFileExist path
  if not exists
    then putStrLn ("  ! Файл не знайдено: " ++ path) >> askPath >>= session
    else do
      raw <- readUtf8 path
      let txt = parseText raw
      printf "Завантажено %s: %d символів, %d речень, %d слів.\n"
        path (length raw) (sentenceCount txt) (length (wordsOf txt))
      menu raw txt

menu :: String -> Text -> IO ()
menu raw txt = do
  putStrLn ""
  putStrLn "1. Показати текст після заміни табуляцій і пробілів"
  putStrLn "2. Перетворення (А): видалити наступні входження першої літери слова"
  putStrLn "3. Перетворення (Б): видалити попередні входження останньої літери слова"
  putStrLn "4. Перетворити слова, введені з клавіатури"
  putStrLn "5. Структура тексту (речення, слова, розділові знаки)"
  putStrLn "6. Автоматичні тести"
  putStrLn "7. Завантажити інший файл"
  putStrLn "0. Вихід"
  choice <- prompt "> "
  case words choice of
    ["0"] -> putStrLn "До побачення!"
    ["1"] -> safely (showNormalized txt) >> again
    ["2"] -> safely (runTransform FirstLetter txt) >> again
    ["3"] -> safely (runTransform LastLetter txt) >> again
    ["4"] -> safely transformInput >> again
    ["5"] -> safely (showStructure txt) >> again
    ["6"] -> safely (runTests raw txt) >> again
    ["7"] -> askPath >>= session
    _ -> putStrLn "  ! Невірний пункт меню" >> again
  where
    again = menu raw txt

-- | Виконує дію, перехоплюючи помилки (наприклад, запису файлу).
safely :: IO () -> IO ()
safely act = do
  r <- try act
  case r of
    Right () -> return ()
    Left e -> putStrLn ("  ! Помилка: " ++ displayException (e :: SomeException))