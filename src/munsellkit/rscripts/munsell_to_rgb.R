#!/usr/bin/env Rscript

library(jsonlite)
library(munsellinterpol)

args <- commandArgs(trailingOnly = TRUE)
munsellName <- args[[1]]
out <- suppressMessages(MunsellTosRGB(munsellName))$RGB
cat(jsonlite::toJSON(out))
