{-# LANGUAGE AllowAmbiguousTypes #-}

-- | Класи типів інформаційної системи.
--
-- Ієрархія:
--   DbEnum   — перелічення, що зберігаються в БД текстовими кодами;
--   Display  — як показати запис користувачу;
--   Entity   — запис, який відповідає таблиці БД (суперкласи: QueryResults,
--              QueryParams, Display);
--   Editable — запис, який можна вводити й коригувати з клавіатури
--              (суперклас: Entity).
module Classes
  ( DbEnum (..)
  , allValues
  , fromCode
  , enumFromDb
  , Display (..)
  , Entity (..)
  , Editable (..)
  ) where

import Data.List (find)
import Data.Text (Text)
import qualified Data.Text as T
import Database.MySQL.Simple (Connection)
import Database.MySQL.Simple.QueryParams (QueryParams)
import Database.MySQL.Simple.QueryResults (QueryResults)

-- | Перелічення (вид матеріалу, статус тощо).
class (Eq a, Enum a, Bounded a) => DbEnum a where
  toCode :: a -> Text
  label  :: a -> String

-- | Усі значення перелічення (завдяки Enum і Bounded).
allValues :: DbEnum a => [a]
allValues = [minBound .. maxBound]

-- | Пошук значення за кодом із БД.
fromCode :: DbEnum a => Text -> Maybe a
fromCode c = find ((== c) . toCode) allValues

-- | Перетворення коду з БД у значення (помилка, якщо код невідомий).
enumFromDb :: DbEnum a => Text -> a
enumFromDb c = maybe (error ("Невідомий код у БД: " ++ T.unpack c)) id (fromCode c)

-- | Відображення запису на екрані.
class Display a where
  -- | Короткий однорядковий вигляд (для списків).
  display :: a -> String
  -- | Детальний вигляд по полях. За замовчуванням — той самий рядок.
  details :: a -> [String]
  details x = [display x]

-- | Сутність = рядок таблиці БД.
-- Знаючи лише ці методи, модуль Repository реалізує CRUD і пошук
-- для БУДЬ-ЯКОЇ таблиці однією узагальненою функцією.
-- Домовленість: перший стовпець таблиці — id; QueryResults читає
-- (id : columns), QueryParams записує columns (без id) у тому ж порядку.
class (QueryResults a, QueryParams a, Display a) => Entity a where
  -- | Ім'я таблиці в БД.
  tableName :: String
  -- | Назва таблиці для користувача.
  entityLabel :: String
  -- | Стовпці, крім id.
  columns :: [String]
  -- | Стовпці, за якими виконується текстовий пошук.
  searchColumns :: [String]
  -- | Порядок сортування (за замовчуванням — за id).
  orderBy :: String
  orderBy = "id"
  -- | Первинний ключ запису.
  entityId :: a -> Int

-- | Сутність, яку користувач може вводити та коригувати.
--   input conn Nothing    — введення нового запису;
--   input conn (Just old) — коригування (старі значення як підказки).
-- Connection потрібне, щоб показати списки для вибору зовнішніх ключів.
class Entity a => Editable a where
  input :: Connection -> Maybe a -> IO a