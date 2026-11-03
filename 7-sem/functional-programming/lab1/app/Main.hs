{-# LANGUAGE AllowAmbiguousTypes #-}

module Main (main) where

import Database.MySQL.Simple (Connection, close)
import System.IO

import Classes
import Db
import Models
import Repository

-- | Друкує всі записи таблиці, що відповідає типу a.
-- Одна функція працює для будь-якого втілення класу Entity.
printAll :: forall a. Entity a => Connection -> IO ()
printAll conn = do
  xs <- findAll @a conn
  putStrLn ""
  putStrLn ("=== " ++ entityLabel @a ++ " (" ++ show (length xs) ++ ") ===")
  mapM_ (putStrLn . display) xs

main :: IO ()
main = do
  hSetEncoding stdout utf8
  conn <- connectDb
  printAll @Category conn
  printAll @Author conn
  printAll @Material conn
  printAll @MaterialAuthor conn
  printAll @PublicationFile conn
  printAll @Reader conn
  printAll @Review conn
  printAll @MaterialView conn
  close conn