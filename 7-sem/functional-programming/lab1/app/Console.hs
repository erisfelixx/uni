-- | Допоміжні функції консольного введення-виведення.
--   Nothing  — створення нового запису (поле обов'язково ввести);
--   Just old — коригування (Enter залишає старе значення).

module Console
  ( prompt
  , askWith
  , askText
  , askEmail
  , askIntRange
  , askDay
  , askDateTime
  , askChoice
  , confirm
  , printTable
  , shorten
  , showDay
  , showDateTime
  , currentLocalTime
  ) where

import Data.Char (isSpace)
import Data.List (dropWhileEnd, intercalate, transpose)
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time
import System.Exit (exitSuccess)
import System.IO (hFlush, isEOF, stdout)
import Text.Read (readMaybe)

-- | Виводить запрошення і зчитує рядок (без пробілів по краях).
-- Якщо введення закінчилось (Ctrl+D) — коректно завершує програму.
prompt :: String -> IO String
prompt msg = do
  putStr msg
  hFlush stdout
  eof <- isEOF
  if eof
    then putStrLn "" >> exitSuccess
    else trim <$> getLine
  where
    trim = dropWhileEnd isSpace . dropWhile isSpace

-- | Універсальне введення значення з перевіркою (функція вищого порядку).
--   parse — розбір рядка (Nothing = помилка);
--   shw   — як показати значення за замовчуванням;
--   err   — повідомлення про помилку;
--   lbl   — назва поля;
--   def   — значення за замовчуванням.
askWith :: (String -> Maybe a) -> (a -> String) -> String -> String -> Maybe a -> IO a
askWith parse shw err lbl def = loop
  where
    hint = maybe "" (\d -> " [" ++ shw d ++ "]") def
    loop = do
      s <- prompt ("  " ++ lbl ++ hint ++ ": ")
      case def of
        Just d | null s -> return d
        _ -> maybe (putStrLn ("    ! " ++ err) >> loop) return (parse s)

-- | Непорожній текст.
askText :: String -> Maybe Text -> IO Text
askText = askWith p T.unpack "Поле не може бути порожнім"
  where
    p s = if null s then Nothing else Just (T.pack s)

-- | E-mail (мінімальна перевірка: є '@' і немає пробілів).
askEmail :: String -> Maybe Text -> IO Text
askEmail = askWith p T.unpack "Некоректний e-mail"
  where
    p s = if '@' `elem` s && not (any isSpace s) then Just (T.pack s) else Nothing

-- | Ціле число в діапазоні [lo, hi].
askIntRange :: Int -> Int -> String -> Maybe Int -> IO Int
askIntRange lo hi = askWith p show ("Введіть ціле число від " ++ show lo ++ " до " ++ show hi)
  where
    p s = case readMaybe s of
      Just n | n >= lo && n <= hi -> Just n
      _ -> Nothing

-- | Дата у форматі РРРР-ММ-ДД.
askDay :: String -> Maybe Day -> IO Day
askDay = askWith (parseTimeM True defaultTimeLocale "%Y-%m-%d") showDay "Формат дати: РРРР-ММ-ДД"

-- | Дата й час у форматі РРРР-ММ-ДД ГГ:ХХ.
askDateTime :: String -> Maybe UTCTime -> IO UTCTime
askDateTime = askWith (parseTimeM True defaultTimeLocale "%Y-%m-%d %H:%M") showDateTime
                      "Формат: РРРР-ММ-ДД ГГ:ХХ"

-- | Вибір одного варіанта зі списку за номером.
askChoice :: (a -> String) -> [a] -> String -> Maybe a -> IO a
askChoice lbl opts title def = do
  putStrLn ("  " ++ title ++ ":")
  mapM_ (\(i, o) -> putStrLn ("    " ++ show i ++ ". " ++ lbl o)) (zip [1 :: Int ..] opts)
  askWith pick lbl ("Оберіть номер від 1 до " ++ show (length opts)) "Номер" def
  where
    pick s = case readMaybe s of
      Just i | i >= 1 && i <= length opts -> Just (opts !! (i - 1))
      _ -> Nothing

-- | Підтвердження дії (так/ні).
confirm :: String -> IO Bool
confirm q = do
  s <- prompt (q ++ " (т/н): ")
  return (s `elem` ["т", "Т", "так", "y", "Y", "yes"])

-- | Виводить таблицю з вирівняними стовпцями.
printTable :: [String] -> [[String]] -> IO ()
printTable hdr rows
  | null rows = putStrLn "  (немає даних)"
  | otherwise = do
      putStrLn (fmt hdr)
      putStrLn (intercalate "-+-" [replicate w '-' | w <- widths])
      mapM_ (putStrLn . fmt) rows
  where
    widths = [maximum (map length col) | col <- transpose (hdr : rows)]
    fmt r = intercalate " | " [c ++ replicate (w - length c) ' ' | (c, w) <- zip r widths]

-- | Обрізає довгий рядок до n символів.
shorten :: Int -> String -> String
shorten n s
  | length s > n = take (n - 1) s ++ "…"
  | otherwise = s

showDay :: Day -> String
showDay = formatTime defaultTimeLocale "%Y-%m-%d"

showDateTime :: UTCTime -> String
showDateTime = formatTime defaultTimeLocale "%Y-%m-%d %H:%M"

-- | Поточний місцевий час. MySQL DATETIME не зберігає часовий пояс,
-- тому записуємо «настінний» місцевий час, як і в тестових даних.
currentLocalTime :: IO UTCTime
currentLocalTime = localTimeToUTC utc . zonedTimeToLocalTime <$> getZonedTime