{-# LANGUAGE OverloadedStrings #-}

-- | Типи даних предметної області "Мережева газета факультету" та їхні втілення (instances) класів:
--   бібліотечних — QueryResults (рядок БД -> тип), QueryParams (тип -> параметри SQL), Param / Result (окремі значення перелічень);
--   власних      — DbEnum, Display, Entity, Editable.
module Models
  ( -- * Перелічення
    AuthorStatus (..)
  , MaterialKind (..)
  , MaterialStatus (..)
    -- * Сутності (таблиці БД)
  , Category (..)
  , Author (..)
  , Material (..)
  , MaterialAuthor (..)
  , PublicationFile (..)
  , Reader (..)
  , Review (..)
  , MaterialView (..)
  ) where

import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (Day, UTCTime)
import Database.MySQL.Simple.Param (Param (..))
import Database.MySQL.Simple.QueryParams (QueryParams (..))
import Database.MySQL.Simple.QueryResults (QueryResults (..))
import Database.MySQL.Simple.Result (Result (..))

import Classes
import Console
import Repository (askOptRef, askRef)



-- Перелічення (алгебраїчні типи-суми)

-- | Статус автора.
data AuthorStatus = Student | Teacher | Staff
  deriving (Eq, Show, Enum, Bounded)

instance DbEnum AuthorStatus where
  toCode Student = "student"
  toCode Teacher = "teacher"
  toCode Staff   = "staff"
  label Student = "студент"
  label Teacher = "викладач"
  label Staff   = "співробітник"

-- Запис у БД — через текстовий код, читання — через розбір коду.
instance Param AuthorStatus where
  render = render . toCode

instance Result AuthorStatus where
  convert f v = enumFromDb (convert f v)

-- | Вид матеріалу: стаття або графічний матеріал.
data MaterialKind = Article | Graphic
  deriving (Eq, Show, Enum, Bounded)

instance DbEnum MaterialKind where
  toCode Article = "article"
  toCode Graphic = "graphic"
  label Article = "стаття"
  label Graphic = "графічний матеріал"

instance Param MaterialKind where
  render = render . toCode

instance Result MaterialKind where
  convert f v = enumFromDb (convert f v)

-- | Статус публікації.
data MaterialStatus = Draft | Published | Archived
  deriving (Eq, Show, Enum, Bounded)

instance DbEnum MaterialStatus where
  toCode Draft     = "draft"
  toCode Published = "published"
  toCode Archived  = "archived"
  label Draft     = "чернетка"
  label Published = "опубліковано"
  label Archived  = "архів"

instance Param MaterialStatus where
  render = render . toCode

instance Result MaterialStatus where
  convert f v = enumFromDb (convert f v)

-- Допоміжні функції відображення
txt :: Text -> String
txt = T.unpack

idTag :: Int -> String
idTag i = "[" ++ show i ++ "]"

-- 1. Рубрика

data Category = Category
  { catId          :: Int
  , catName        :: Text
  , catDescription :: Text
  } deriving (Show)

-- Рядок БД (id, name, description) -> Category.
-- Використовуємо готове втілення QueryResults для кортежу.
instance QueryResults Category where
  convertResults fs vs = Category a b c
    where (a, b, c) = convertResults fs vs

-- Category -> параметри для INSERT/UPDATE (у порядку columns, без id).
instance QueryParams Category where
  renderParams c = [render (catName c), render (catDescription c)]

instance Display Category where
  display c = idTag (catId c) ++ " " ++ txt (catName c)
  details c =
    [ "ID:    " ++ show (catId c)
    , "Назва: " ++ txt (catName c)
    , "Опис:  " ++ txt (catDescription c)
    ]

instance Entity Category where
  tableName     = "categories"
  entityLabel   = "Рубрики"
  columns       = ["name", "description"]
  searchColumns = ["name", "description"]
  orderBy       = "name"
  entityId      = catId

-- Поля вводяться по черзі зліва направо.
instance Editable Category where
  input _ old = Category (maybe 0 catId old)
    <$> askText "Назва рубрики" (catName <$> old)
    <*> askText "Опис"          (catDescription <$> old)


-- 2. Автор

data Author = Author
  { authorId     :: Int
  , authorName   :: Text
  , authorEmail  :: Text
  , authorStatus :: AuthorStatus
  , authorUnit   :: Text          -- група або кафедра
  } deriving (Show)

instance QueryResults Author where
  convertResults fs vs = Author a b c d e
    where (a, b, c, d, e) = convertResults fs vs

instance QueryParams Author where
  renderParams a =
    [render (authorName a), render (authorEmail a), render (authorStatus a), render (authorUnit a)]

instance Display Author where
  display a = idTag (authorId a) ++ " " ++ txt (authorName a)
           ++ " (" ++ label (authorStatus a) ++ ", " ++ txt (authorUnit a) ++ ")"
  details a =
    [ "ID:              " ++ show (authorId a)
    , "ПІБ:             " ++ txt (authorName a)
    , "E-mail:          " ++ txt (authorEmail a)
    , "Статус:          " ++ label (authorStatus a)
    , "Група / кафедра: " ++ txt (authorUnit a)
    ]

instance Entity Author where
  tableName     = "authors"
  entityLabel   = "Автори"
  columns       = ["full_name", "email", "status", "unit"]
  searchColumns = ["full_name", "email", "unit"]
  orderBy       = "full_name"
  entityId      = authorId

instance Editable Author where
  input _ old = Author (maybe 0 authorId old)
    <$> askText   "ПІБ"    (authorName <$> old)
    <*> askEmail  "E-mail" (authorEmail <$> old)
    <*> askChoice label allValues "Статус автора" (authorStatus <$> old)
    <*> askText   "Група або кафедра" (authorUnit <$> old)



-- 3. Матеріал (стаття або графічний матеріал)

data Material = Material
  { matId          :: Int
  , matTitle       :: Text
  , matKind        :: MaterialKind
  , matAnnotation  :: Text
  , matCategoryId  :: Int
  , matPublishedOn :: Day
  , matStatus      :: MaterialStatus
  } deriving (Show)

instance QueryResults Material where
  convertResults fs vs = Material a b c d e f g
    where (a, b, c, d, e, f, g) = convertResults fs vs

instance QueryParams Material where
  renderParams m =
    [ render (matTitle m), render (matKind m), render (matAnnotation m)
    , render (matCategoryId m), render (matPublishedOn m), render (matStatus m)
    ]

instance Display Material where
  display m = idTag (matId m) ++ " " ++ shorten 55 (txt (matTitle m))
           ++ " — " ++ label (matKind m) ++ ", " ++ label (matStatus m)
           ++ ", " ++ showDay (matPublishedOn m)
  details m =
    [ "ID:              " ++ show (matId m)
    , "Назва:           " ++ txt (matTitle m)
    , "Вид:             " ++ label (matKind m)
    , "Анотація:        " ++ txt (matAnnotation m)
    , "Рубрика (id):    " ++ show (matCategoryId m)
    , "Дата публікації: " ++ showDay (matPublishedOn m)
    , "Статус:          " ++ label (matStatus m)
    ]

instance Entity Material where
  tableName     = "materials"
  entityLabel   = "Матеріали"
  columns       = ["title", "kind", "annotation", "category_id", "published_on", "status"]
  searchColumns = ["title", "annotation"]
  orderBy       = "published_on DESC"
  entityId      = matId

instance Editable Material where
  input conn old = Material (maybe 0 matId old)
    <$> askText "Назва матеріалу" (matTitle <$> old)
    <*> askChoice label allValues "Вид матеріалу" (matKind <$> old)
    <*> askText "Текст анотації" (matAnnotation <$> old)
    <*> askRef @Category conn "Рубрика" (matCategoryId <$> old)
    <*> askDay "Дата публікації (РРРР-ММ-ДД)" (matPublishedOn <$> old)
    <*> askChoice label allValues "Статус" (matStatus <$> old)


-- 4. Автор матеріалу (зв'язок "багато-до-багатьох")

data MaterialAuthor = MaterialAuthor
  { maId         :: Int
  , maMaterialId :: Int
  , maAuthorId   :: Int
  , maRole       :: Text          -- автор тексту, фотограф, ...
  } deriving (Show)

instance QueryResults MaterialAuthor where
  convertResults fs vs = MaterialAuthor a b c d
    where (a, b, c, d) = convertResults fs vs

instance QueryParams MaterialAuthor where
  renderParams x = [render (maMaterialId x), render (maAuthorId x), render (maRole x)]

instance Display MaterialAuthor where
  display x = idTag (maId x) ++ " матеріал #" ++ show (maMaterialId x)
           ++ " — автор #" ++ show (maAuthorId x) ++ " (" ++ txt (maRole x) ++ ")"

instance Entity MaterialAuthor where
  tableName     = "material_authors"
  entityLabel   = "Автори матеріалів"
  columns       = ["material_id", "author_id", "role"]
  searchColumns = ["role"]
  orderBy       = "material_id, author_id"
  entityId      = maId

instance Editable MaterialAuthor where
  input conn old = MaterialAuthor (maybe 0 maId old)
    <$> askRef @Material conn "Матеріал" (maMaterialId <$> old)
    <*> askRef @Author conn "Автор" (maAuthorId <$> old)
    <*> askText "Роль (автор тексту, фотограф, ...)" (maRole <$> old)



-- 5. Файл публікації

data PublicationFile = PublicationFile
  { fileId         :: Int
  , fileMaterialId :: Int
  , filePath       :: Text        
  , fileFormat     :: Text
  , fileSizeKb     :: Int
  , fileUploadedOn :: Day
  } deriving (Show)

instance QueryResults PublicationFile where
  convertResults fs vs = PublicationFile a b c d e f
    where (a, b, c, d, e, f) = convertResults fs vs

instance QueryParams PublicationFile where
  renderParams x =
    [ render (fileMaterialId x), render (filePath x), render (fileFormat x)
    , render (fileSizeKb x), render (fileUploadedOn x)
    ]

instance Display PublicationFile where
  display x = idTag (fileId x) ++ " " ++ txt (filePath x)
           ++ " (" ++ txt (fileFormat x) ++ ", " ++ show (fileSizeKb x) ++ " КБ)"
           ++ " — матеріал #" ++ show (fileMaterialId x)
  details x =
    [ "ID:                " ++ show (fileId x)
    , "Матеріал (id):     " ++ show (fileMaterialId x)
    , "Шлях / адреса:     " ++ txt (filePath x)
    , "Формат:            " ++ txt (fileFormat x)
    , "Розмір, КБ:        " ++ show (fileSizeKb x)
    , "Дата завантаження: " ++ showDay (fileUploadedOn x)
    ]

instance Entity PublicationFile where
  tableName     = "publication_files"
  entityLabel   = "Файли публікацій"
  columns       = ["material_id", "file_path", "file_format", "size_kb", "uploaded_on"]
  searchColumns = ["file_path", "file_format"]
  orderBy       = "material_id, id"
  entityId      = fileId

instance Editable PublicationFile where
  input conn old = PublicationFile (maybe 0 fileId old)
    <$> askRef @Material conn "Матеріал" (fileMaterialId <$> old)
    <*> askText "Шлях до файлу або адреса в мережі" (filePath <$> old)
    <*> askText "Формат (pdf, docx, jpg, ...)" (fileFormat <$> old)
    <*> askIntRange 0 maxBound "Розмір, КБ" (fileSizeKb <$> old)
    <*> askDay "Дата завантаження (РРРР-ММ-ДД)" (fileUploadedOn <$> old)


-- 6. Читач

data Reader = Reader
  { readerId           :: Int
  , readerName         :: Text
  , readerEmail        :: Text
  , readerGroup        :: Text
  , readerRegisteredOn :: Day
  } deriving (Show)

instance QueryResults Reader where
  convertResults fs vs = Reader a b c d e
    where (a, b, c, d, e) = convertResults fs vs

instance QueryParams Reader where
  renderParams r =
    [render (readerName r), render (readerEmail r), render (readerGroup r), render (readerRegisteredOn r)]

instance Display Reader where
  display r = idTag (readerId r) ++ " " ++ txt (readerName r) ++ " (" ++ txt (readerGroup r) ++ ")"
  details r =
    [ "ID:               " ++ show (readerId r)
    , "ПІБ:              " ++ txt (readerName r)
    , "E-mail:           " ++ txt (readerEmail r)
    , "Група / посада:   " ++ txt (readerGroup r)
    , "Дата реєстрації:  " ++ showDay (readerRegisteredOn r)
    ]

instance Entity Reader where
  tableName     = "readers"
  entityLabel   = "Читачі"
  columns       = ["full_name", "email", "academic_group", "registered_on"]
  searchColumns = ["full_name", "email", "academic_group"]
  orderBy       = "full_name"
  entityId      = readerId

instance Editable Reader where
  input _ old = Reader (maybe 0 readerId old)
    <$> askText  "ПІБ" (readerName <$> old)
    <*> askEmail "E-mail" (readerEmail <$> old)
    <*> askText  "Група або посада" (readerGroup <$> old)
    <*> askDay   "Дата реєстрації (РРРР-ММ-ДД)" (readerRegisteredOn <$> old)



-- 7. Відгук читача

data Review = Review
  { reviewId         :: Int
  , reviewMaterialId :: Int
  , reviewReaderId   :: Int
  , reviewRating     :: Int       
  , reviewComment    :: Text
  , reviewCreatedOn  :: Day
  } deriving (Show)

instance QueryResults Review where
  convertResults fs vs = Review a b c d e f
    where (a, b, c, d, e, f) = convertResults fs vs

instance QueryParams Review where
  renderParams r =
    [ render (reviewMaterialId r), render (reviewReaderId r), render (reviewRating r)
    , render (reviewComment r), render (reviewCreatedOn r)
    ]

-- | Оцінка зірочками: 4 -> "★★★★☆".
stars :: Int -> String
stars n = replicate n '★' ++ replicate (5 - n) '☆'

instance Display Review where
  display r = idTag (reviewId r) ++ " " ++ stars (reviewRating r)
           ++ " матеріал #" ++ show (reviewMaterialId r)
           ++ ", читач #" ++ show (reviewReaderId r)
           ++ ": " ++ shorten 50 (txt (reviewComment r))
  details r =
    [ "ID:            " ++ show (reviewId r)
    , "Матеріал (id): " ++ show (reviewMaterialId r)
    , "Читач (id):    " ++ show (reviewReaderId r)
    , "Оцінка:        " ++ stars (reviewRating r) ++ " (" ++ show (reviewRating r) ++ ")"
    , "Відгук:        " ++ txt (reviewComment r)
    , "Дата:          " ++ showDay (reviewCreatedOn r)
    ]

instance Entity Review where
  tableName     = "reviews"
  entityLabel   = "Відгуки"
  columns       = ["material_id", "reader_id", "rating", "comment", "created_on"]
  searchColumns = ["comment"]
  orderBy       = "created_on DESC"
  entityId      = reviewId

instance Editable Review where
  input conn old = Review (maybe 0 reviewId old)
    <$> askRef @Material conn "Матеріал" (reviewMaterialId <$> old)
    <*> askRef @Reader conn "Читач" (reviewReaderId <$> old)
    <*> askIntRange 1 5 "Оцінка (1-5)" (reviewRating <$> old)
    <*> askText "Текст відгуку" (reviewComment <$> old)
    <*> askDay "Дата (РРРР-ММ-ДД)" (reviewCreatedOn <$> old)



-- 8. Перегляд матеріалу (для статистики)


data MaterialView = MaterialView
  { viewId         :: Int
  , viewMaterialId :: Int
  , viewReaderId   :: Maybe Int   -- Nothing = анонімний перегляд (NULL у БД)
  , viewViewedAt   :: UTCTime
  } deriving (Show)

instance QueryResults MaterialView where
  convertResults fs vs = MaterialView a b c d
    where (a, b, c, d) = convertResults fs vs

instance QueryParams MaterialView where
  renderParams v = [render (viewMaterialId v), render (viewReaderId v), render (viewViewedAt v)]

instance Display MaterialView where
  display v = idTag (viewId v) ++ " матеріал #" ++ show (viewMaterialId v)
           ++ ", " ++ maybe "анонімний читач" (\r -> "читач #" ++ show r) (viewReaderId v)
           ++ ", " ++ showDateTime (viewViewedAt v)

instance Entity MaterialView where
  tableName     = "material_views"
  entityLabel   = "Перегляди"
  columns       = ["material_id", "reader_id", "viewed_at"]
  searchColumns = ["viewed_at"]
  orderBy       = "viewed_at DESC"
  entityId      = viewId

instance Editable MaterialView where
  input conn old = do
    now <- currentLocalTime
    MaterialView (maybe 0 viewId old)
      <$> askRef @Material conn "Матеріал" (viewMaterialId <$> old)
      <*> askOptRef @Reader conn "Читач" (viewReaderId <$> old)
      <*> askDateTime "Дата й час (РРРР-ММ-ДД ГГ:ХХ)" (Just (maybe now viewViewedAt old))