{-# LANGUAGE OverloadedStrings #-}

-- | Підключення до бази даних MySQL "newspaper"
module Db (connectDb) where

import Database.MySQL.Simple

-- | Параметри підключення
dbInfo :: ConnectInfo
dbInfo = defaultConnectInfo
  { connectHost     = "127.0.0.1"
  , connectPort     = 3306
  , connectUser     = "news"
  , connectPassword = "news123"
  , connectDatabase = "newspaper"
  }

-- | Відкриває з'єднання та вмикає кодування utf8mb4, щоб коректно передавалися українські тексти.
connectDb :: IO Connection
connectDb = do
  conn <- connect dbInfo
  _ <- execute_ conn "SET NAMES utf8mb4"
  return conn