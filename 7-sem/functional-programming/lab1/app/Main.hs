{-# LANGUAGE AllowAmbiguousTypes #-}

-- | Інформаційна система "Мережева газета факультету".
-- Головний модуль: консольне меню.

module Main (main) where

import Control.Exception (SomeException, displayException, fromException, throwIO, try)
import Control.Monad (when)
import Database.MySQL.Simple (Connection, close)
import System.Exit (ExitCode)
import System.IO
import Text.Read (readMaybe)

import Classes
import Console
import Db
import Models
import Repository
import Stats

main :: IO ()
main = do
  hSetEncoding stdout utf8
  hSetEncoding stdin utf8
  hSetBuffering stdout NoBuffering
  conn <- connectDb
  mainMenu conn
  close conn
  putStrLn "До побачення!"


-- Універсальне меню

-- | Меню: список (назва пункту, дія). Пункт 0 — повернення.
runMenu :: String -> String -> [(String, IO ())] -> IO ()
runMenu title exitLabel items = loop
  where
    loop = do
      putStrLn ""
      putStrLn ("========== " ++ title ++ " ==========")
      mapM_ (\(i, (l, _)) -> putStrLn (show i ++ ". " ++ l)) (zip [1 :: Int ..] items)
      putStrLn ("0. " ++ exitLabel)
      s <- prompt "> "
      case readMaybe s :: Maybe Int of
        Just 0 -> return ()
        Just i | i >= 1 && i <= length items -> safely (snd (items !! (i - 1))) >> loop
        _ -> putStrLn "  ! Невірний пункт меню" >> loop

-- | Виконує дію, перехоплюючи помилки (наприклад, порушення зовнішнього ключа).
-- (Виняток завершення програми (Ctrl+D) пропускаємо далі.)
safely :: IO () -> IO ()
safely act = do
  r <- try act
  case r of
    Right () -> return ()
    Left e -> case fromException e of
      Just ec -> throwIO (ec :: ExitCode)
      Nothing -> putStrLn ("  ! Помилка: " ++ displayException (e :: SomeException))

-- | Друк списку записів.
printRecords :: Display a => [a] -> IO ()
printRecords [] = putStrLn "  (записів не знайдено)"
printRecords xs = do
  mapM_ (putStrLn . ("  " ++) . display) xs
  putStrLn ("  Усього: " ++ show (length xs))

askId :: IO Int
askId = askIntRange 1 maxBound "id запису" Nothing

notFound :: IO ()
notFound = putStrLn "  Запис з таким id не знайдено"

-- | Меню роботи з будь-якою таблицею: перегляд, пошук, введення, коригування, видалення.
-- Одна функція для всіх 8 таблиць — тип таблиці задається через TypeApplications: entityMenu @Material.
entityMenu :: forall a. Editable a => Connection -> IO ()
entityMenu conn = runMenu (entityLabel @a) "Назад"
  [ ("Показати всі", findAll @a conn >>= printRecords)
  , ("Пошук за текстом", do
        t <- askText "Текст для пошуку" Nothing
        searchText @a conn t >>= printRecords)
  , ("Детально за id", do
        i <- askId
        findById @a conn i >>= maybe notFound (mapM_ (putStrLn . ("  " ++)) . details))
  , ("Додати запис", do
        putStrLn "  Введення нового запису:"
        x <- input @a conn Nothing
        newId <- insertEntity conn x
        putStrLn ("  Додано запис з id = " ++ show newId))
  , ("Редагувати запис", do
        i <- askId
        mx <- findById @a conn i
        case mx of
          Nothing -> notFound
          Just old -> do
            putStrLn ("  Редагування: " ++ display old)
            putStrLn "  (Enter — залишити поточне значення у [дужках])"
            new <- input conn (Just old)
            updateEntity conn new
            putStrLn "  Зміни збережено")
  , ("Видалити запис", do
        i <- askId
        mx <- findById @a conn i
        case mx of
          Nothing -> notFound
          Just x -> do
            putStrLn ("  " ++ display x)
            ok <- confirm "  Видалити цей запис?"
            when ok $ do
              _ <- deleteEntity @a conn i
              putStrLn "  Запис видалено")
  ]


-- Меню програми

mainMenu :: Connection -> IO ()
mainMenu conn = runMenu "Мережева газета факультету" "Вихід"
  [ ("Матеріали (статті та графіка)",              entityMenu @Material conn)
  , ("Рубрики",                                     entityMenu @Category conn)
  , ("Автори",                                      entityMenu @Author conn)
  , ("Автори матеріалів (зв'язки)",                 entityMenu @MaterialAuthor conn)
  , ("Файли публікацій",                            entityMenu @PublicationFile conn)
  , ("Читачі",                                      entityMenu @Reader conn)
  , ("Відгуки читачів",                             entityMenu @Review conn)
  , ("Перегляди",                                   entityMenu @MaterialView conn)
  , ("Читати матеріал (картка + реєстрація перегляду)", readMaterial conn)
  , ("Статистика",                                  statsMenu conn)
  ]

statsMenu :: Connection -> IO ()
statsMenu conn = runMenu "Статистика" "Назад"
  [ ("Статистика окремого матеріалу (картка)", do
        mid <- askRef @Material conn "Матеріал" Nothing
        materialCard conn mid)
  , ("Топ матеріалів за переглядами", topByViews conn)
  , ("Рейтинг матеріалів за оцінками", topByRating conn)
  , ("Статистика рубрик",              categoryStats conn)
  , ("Активність читачів",             readerActivity conn)
  , ("Продуктивність авторів",         authorStats conn)
  , ("Загальна статистика газети",     overview conn)
  ]