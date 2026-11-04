{-# LANGUAGE OverloadedStrings #-}

-- | Статистика про матеріали газети та "читацький режим".
-- Статистика не зберігається окремо, а щоразу обчислюється SQL-запитами з таблиць material_views і reviews.
module Stats
  ( materialCard
  , readMaterial
  , topByViews
  , topByRating
  , categoryStats
  , readerActivity
  , authorStats
  , overview
  ) where

import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (Day)
import Database.MySQL.Simple
import Text.Printf (printf)

import Classes
import Console
import Models
import Repository

txt :: Text -> String
txt = T.unpack

-- | Середня оцінка або прочерк, якщо відгуків немає.
showAvg :: Maybe Double -> String
showAvg = maybe "—" (printf "%.2f")



-- Картка матеріалу: усі дані + статистика по ньому

materialCard :: Connection -> Int -> IO ()
materialCard conn mid = do
  mm <- findById @Material conn mid
  case mm of
    Nothing -> putStrLn "  Матеріал не знайдено"
    Just m -> do
      cats <- query conn "SELECT name FROM categories WHERE id = ?"
                (Only (matCategoryId m)) :: IO [Only Text]
      authors <- query conn
        "SELECT a.full_name, ma.role FROM material_authors ma \
        \JOIN authors a ON a.id = ma.author_id \
        \WHERE ma.material_id = ? ORDER BY a.full_name"
        (Only mid) :: IO [(Text, Text)]
      files <- query conn
        "SELECT file_path, file_format, size_kb FROM publication_files \
        \WHERE material_id = ? ORDER BY id"
        (Only mid) :: IO [(Text, Text, Int)]
      reviews <- query conn
        "SELECT r.full_name, rv.rating, rv.comment, rv.created_on FROM reviews rv \
        \JOIN readers r ON r.id = rv.reader_id \
        \WHERE rv.material_id = ? ORDER BY rv.created_on"
        (Only mid) :: IO [(Text, Int, Text, Day)]
      [(views, uniqueReaders, anonymous)] <- query conn
        "SELECT COUNT(*), COUNT(DISTINCT reader_id), \
        \CAST(COALESCE(SUM(reader_id IS NULL), 0) AS SIGNED) \
        \FROM material_views WHERE material_id = ?"
        (Only mid) :: IO [(Int, Int, Int)]
      [Only avgRating] <- query conn
        "SELECT CAST(AVG(rating) AS DOUBLE) FROM reviews WHERE material_id = ?"
        (Only mid) :: IO [Only (Maybe Double)]
      byDay <- query conn
        "SELECT DATE(viewed_at), COUNT(*) FROM material_views \
        \WHERE material_id = ? GROUP BY DATE(viewed_at) ORDER BY DATE(viewed_at)"
        (Only mid) :: IO [(Day, Int)]

      putStrLn ""
      putStrLn ("==== " ++ txt (matTitle m) ++ " ====")
      putStrLn ("  Вид:       " ++ label (matKind m))
      putStrLn ("  Рубрика:   " ++ concatMap (\(Only c) -> txt c) cats)
      putStrLn ("  Дата:      " ++ showDay (matPublishedOn m) ++ ", статус: " ++ label (matStatus m))
      putStrLn ("  Анотація:  " ++ txt (matAnnotation m))

      putStrLn "\n  Автори:"
      if null authors
        then putStrLn "    (не вказано)"
        else mapM_ (\(n, r) -> putStrLn ("    • " ++ txt n ++ " — " ++ txt r)) authors

      putStrLn "\n  Файли публікації:"
      if null files
        then putStrLn "    (немає)"
        else mapM_ (\(p, f, s) -> putStrLn ("    • " ++ txt p ++ " (" ++ txt f ++ ", " ++ show s ++ " КБ)")) files

      putStrLn "\n  Статистика:"
      putStrLn ("    Переглядів усього:     " ++ show views)
      putStrLn ("    Унікальних читачів:    " ++ show uniqueReaders)
      putStrLn ("    Анонімних переглядів:  " ++ show anonymous)
      putStrLn ("    Відгуків:              " ++ show (length reviews))
      putStrLn ("    Середня оцінка:        " ++ showAvg avgRating)
      putStrLn "    Перегляди по днях:"
      if null byDay
        then putStrLn "      (немає)"
        else mapM_ (\(d, n) -> putStrLn ("      " ++ showDay d ++ "  " ++ replicate n '█' ++ " " ++ show n)) byDay

      putStrLn "\n  Відгуки читачів:"
      if null reviews
        then putStrLn "    (немає)"
        else mapM_ (\(n, r, c, d) -> putStrLn
                      ("    " ++ showDay d ++ " " ++ replicate r '★' ++ replicate (5 - r) '☆'
                       ++ " " ++ txt n ++ ": " ++ txt c)) reviews

-- | "Читацький режим": читач відкриває матеріал — реєструється перегляд
-- (час — NOW() сервера БД), після чого показується картка матеріалу.
readMaterial :: Connection -> IO ()
readMaterial conn = do
  mid <- askRef @Material conn "Матеріал для читання" Nothing
  rid <- askOptRef @Reader conn "Хто читає" Nothing
  _ <- execute conn
         "INSERT INTO material_views (material_id, reader_id, viewed_at) VALUES (?, ?, NOW())"
         (mid, rid)
  putStrLn "  Перегляд зареєстровано."
  materialCard conn mid


-- Звіти

-- | Топ-N матеріалів за кількістю переглядів.
topByViews :: Connection -> IO ()
topByViews conn = do
  n <- askIntRange 1 100 "Скільки матеріалів показати" (Just 5)
  rows <- query conn
    "SELECT m.id, m.title, COUNT(v.id) AS cnt, COUNT(DISTINCT v.reader_id) \
    \FROM materials m LEFT JOIN material_views v ON v.material_id = m.id \
    \GROUP BY m.id, m.title ORDER BY cnt DESC, m.id LIMIT ?"
    (Only n) :: IO [(Int, Text, Int, Int)]
  printTable ["#", "id", "Матеріал", "Переглядів", "Унік. читачів"]
    [ [show i, show mid, shorten 50 (txt t), show c, show u]
    | (i, (mid, t, c, u)) <- zip [1 :: Int ..] rows ]

-- | Рейтинг матеріалів за середньою оцінкою відгуків.
topByRating :: Connection -> IO ()
topByRating conn = do
  rows <- query_ conn
    "SELECT m.id, m.title, CAST(AVG(r.rating) AS DOUBLE) AS avg_r, COUNT(r.id) AS cnt \
    \FROM materials m JOIN reviews r ON r.material_id = m.id \
    \GROUP BY m.id, m.title ORDER BY avg_r DESC, cnt DESC" :: IO [(Int, Text, Double, Int)]
  printTable ["#", "id", "Матеріал", "Сер. оцінка", "Відгуків"]
    [ [show i, show mid, shorten 50 (txt t), printf "%.2f" a, show c]
    | (i, (mid, t, a, c)) <- zip [1 :: Int ..] rows ]

-- | Кількість матеріалів і переглядів по рубриках.
categoryStats :: Connection -> IO ()
categoryStats conn = do
  rows <- query_ conn
    "SELECT c.name, \
    \(SELECT COUNT(*) FROM materials m WHERE m.category_id = c.id), \
    \(SELECT COUNT(*) FROM material_views v JOIN materials m ON m.id = v.material_id \
    \  WHERE m.category_id = c.id), \
    \(SELECT CAST(AVG(r.rating) AS DOUBLE) FROM reviews r JOIN materials m ON m.id = r.material_id \
    \  WHERE m.category_id = c.id) \
    \FROM categories c ORDER BY c.name" :: IO [(Text, Int, Int, Maybe Double)]
  printTable ["Рубрика", "Матеріалів", "Переглядів", "Сер. оцінка"]
    [ [txt c, show m, show v, showAvg a] | (c, m, v, a) <- rows ]

-- | Активність читачів: перегляди та відгуки.
readerActivity :: Connection -> IO ()
readerActivity conn = do
  rows <- query_ conn
    "SELECT r.full_name, r.academic_group, \
    \(SELECT COUNT(*) FROM material_views v WHERE v.reader_id = r.id) AS views_cnt, \
    \(SELECT COUNT(*) FROM reviews rv WHERE rv.reader_id = r.id) AS reviews_cnt \
    \FROM readers r ORDER BY views_cnt DESC, reviews_cnt DESC, r.full_name"
    :: IO [(Text, Text, Int, Int)]
  printTable ["Читач", "Група", "Переглядів", "Відгуків"]
    [ [txt n, txt g, show v, show c] | (n, g, v, c) <- rows ]

-- | Продуктивність авторів: кількість матеріалів і переглядів їхніх матеріалів.
authorStats :: Connection -> IO ()
authorStats conn = do
  rows <- query_ conn
    "SELECT a.full_name, a.status, COUNT(DISTINCT ma.material_id), COUNT(v.id) AS views_cnt \
    \FROM authors a \
    \LEFT JOIN material_authors ma ON ma.author_id = a.id \
    \LEFT JOIN material_views v ON v.material_id = ma.material_id \
    \GROUP BY a.id, a.full_name, a.status ORDER BY views_cnt DESC, a.full_name"
    :: IO [(Text, AuthorStatus, Int, Int)]
  printTable ["Автор", "Статус", "Матеріалів", "Переглядів їх матеріалів"]
    [ [txt n, label s, show m, show v] | (n, s, m, v) <- rows ]

-- | Загальна зведена статистика газети.
overview :: Connection -> IO ()
overview conn = do
  [(mats, published, authorsN, readersN, reviewsN, viewsN, avgR)] <- query_ conn
    "SELECT (SELECT COUNT(*) FROM materials), \
    \(SELECT COUNT(*) FROM materials WHERE status = 'published'), \
    \(SELECT COUNT(*) FROM authors), \
    \(SELECT COUNT(*) FROM readers), \
    \(SELECT COUNT(*) FROM reviews), \
    \(SELECT COUNT(*) FROM material_views), \
    \(SELECT CAST(AVG(rating) AS DOUBLE) FROM reviews)"
    :: IO [(Int, Int, Int, Int, Int, Int, Maybe Double)]
  putStrLn ""
  putStrLn ("  Матеріалів:            " ++ show mats ++ " (опубліковано: " ++ show published ++ ")")
  putStrLn ("  Авторів:               " ++ show authorsN)
  putStrLn ("  Читачів:               " ++ show readersN)
  putStrLn ("  Відгуків:              " ++ show reviewsN)
  putStrLn ("  Переглядів:            " ++ show viewsN)
  putStrLn ("  Середня оцінка газети: " ++ showAvg avgR)