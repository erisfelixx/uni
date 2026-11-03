{-# LANGUAGE AllowAmbiguousTypes #-}

-- | Узагальнені операції з БД (CRUD і пошук) для будь-якого типу, що є втіленням класу Entity. 
-- SQL-запити будуються з методів класу, тому для нової таблиці достатньо написати instance Entity.
module Repository
  ( Params (..)
  , findAll
  , findById
  , searchText
  , insertEntity
  , updateEntity
  , deleteEntity
  , askRef
  , askOptRef
  ) where

import Data.List (intercalate)
import Data.Maybe (listToMaybe)
import Data.String (fromString)
import Data.Text (Text)
import qualified Data.Text as T
import Database.MySQL.Simple
import Database.MySQL.Simple.Param (Action, render)
import Database.MySQL.Simple.QueryParams (QueryParams (..))
import Text.Read (readMaybe)

import Classes
import Console (askWith)

-- | Довільний список параметрів запиту.
-- Власне втілення QueryParams дозволяє передати змінну кількість "?".
newtype Params = Params [Action]

instance QueryParams Params where
  renderParams (Params xs) = xs

-- | SELECT id, <стовпці> FROM <таблиця>
selectSql :: forall a. Entity a => String
selectSql = "SELECT id, " ++ intercalate ", " (columns @a) ++ " FROM " ++ tableName @a

-- | Усі записи таблиці.
findAll :: forall a. Entity a => Connection -> IO [a]
findAll conn = query_ conn (fromString (selectSql @a ++ " ORDER BY " ++ orderBy @a))

-- | Запис за первинним ключем.
findById :: forall a. Entity a => Connection -> Int -> IO (Maybe a)
findById conn i =
  listToMaybe <$> query conn (fromString (selectSql @a ++ " WHERE id = ?")) (Only i)

-- | Пошук підрядка в усіх стовпцях searchColumns (LIKE '%текст%').
searchText :: forall a. Entity a => Connection -> Text -> IO [a]
searchText conn term = query conn (fromString sql) (Params (map (const (render pat)) cols))
  where
    cols = searchColumns @a
    pat  = T.concat [T.pack "%", term, T.pack "%"]
    sql  = selectSql @a
        ++ " WHERE " ++ intercalate " OR " [c ++ " LIKE ?" | c <- cols]
        ++ " ORDER BY " ++ orderBy @a

-- | Додає запис, повертає id нового рядка.
insertEntity :: forall a. Entity a => Connection -> a -> IO Int
insertEntity conn x = do
  _ <- execute conn (fromString sql) x
  fromIntegral <$> insertID conn
  where
    cols = columns @a
    sql  = "INSERT INTO " ++ tableName @a
        ++ " (" ++ intercalate ", " cols ++ ")"
        ++ " VALUES (" ++ intercalate ", " (map (const "?") cols) ++ ")"

-- | Оновлює всі поля запису за його id.
updateEntity :: forall a. Entity a => Connection -> a -> IO ()
updateEntity conn x = do
  _ <- execute conn (fromString sql) (Params (renderParams x ++ [render (entityId x)]))
  return ()
  where
    sql = "UPDATE " ++ tableName @a
       ++ " SET " ++ intercalate ", " [c ++ " = ?" | c <- columns @a]
       ++ " WHERE id = ?"

-- | Видаляє запис за id. True — якщо запис існував.
deleteEntity :: forall a. Entity a => Connection -> Int -> IO Bool
deleteEntity conn i = do
  n <- execute conn (fromString ("DELETE FROM " ++ tableName @a ++ " WHERE id = ?")) (Only i)
  return (n > 0)

-- | Введення зовнішнього ключа: показує записи таблиці b
-- і дозволяє ввести лише id, що існує.
askRef :: forall b. Entity b => Connection -> String -> Maybe Int -> IO Int
askRef conn lbl def = do
  xs <- findAll @b conn
  putStrLn ("  " ++ entityLabel @b ++ ":")
  mapM_ (\x -> putStrLn ("    " ++ display x)) xs
  let ids = map entityId xs
      p s = case readMaybe s of
        Just i | i `elem` ids -> Just i
        _ -> Nothing
  askWith p show "Немає запису з таким id" (lbl ++ " (id)") def

-- | Необов'язковий зовнішній ключ ('-' або порожньо = немає).
askOptRef :: forall b. Entity b => Connection -> String -> Maybe (Maybe Int) -> IO (Maybe Int)
askOptRef conn lbl def = do
  xs <- findAll @b conn
  putStrLn ("  " ++ entityLabel @b ++ ":")
  mapM_ (\x -> putStrLn ("    " ++ display x)) xs
  let ids = map entityId xs
      p "-" = Just Nothing
      p ""  = Just Nothing
      p s = case readMaybe s of
        Just i | i `elem` ids -> Just (Just i)
        _ -> Nothing
  askWith p (maybe "-" show) "Введіть id зі списку або '-'" (lbl ++ " (id або '-')") def