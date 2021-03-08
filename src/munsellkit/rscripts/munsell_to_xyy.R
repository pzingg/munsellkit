#!/usr/bin/env Rscript

library(jsonlite)
library(munsellinterpol)

args <- commandArgs(trailingOnly = TRUE)
munsellName <- args[[1]]
xyC = "NBS"
if (length(args) > 1) {
  xyC = args[[2]]
}
out <- suppressMessages(MunsellToxyY(munsellName, xyC=xyC))$xyY
cat(jsonlite::toJSON(out))
