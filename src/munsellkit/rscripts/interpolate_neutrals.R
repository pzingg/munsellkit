#!/usr/bin/env Rscript

library(munsellinterpol)

interpolate_neutrals <- function() {
  grays <- paste0("N", seq(0, 10, 0.5))
  MunsellTosRGB(grays)
}

rgb <- interpolate_neutrals()
write.csv(rgb, "munsell_neutrals.csv")
