#!/usr/bin/env Rscript

library(optparse)
library(Nozzle.R1)
options(stringsAsFactors=FALSE)

################################################################################
## Parse command line arguments
################################################################################
# @param infilemap
#  A 2-column TSV table of the files to be read by this report, with each row
#  representing key=value pairs where
#      key   (column 1) is the name of the variable to be created
#      value (column 2) is the name of the file (content)
#  This is an experiment, where instead of accepting N arguments, one for each
#  input file, the report expects 1 argument that lists all N files.  This 
#  applies only to file inputs, and when reports expect more than 1 of such
#  (the overwhelmingly common case).  Reports may of course accept additional
#  (scalar-valued) args such as -title"some_report_title" and so forth.

option.list <- list(make_option(c("-i", "--infilemap"),
                                help=paste("file specifying how the input",
                                           "files map to parameters for this",
                                           "report"))
)

args <- parse_args(OptionParser(option_list=option.list,
                                usage="Rscript %prog [options]"),
                                print_help_and_exit=FALSE)

main <- function(args)
{
  ##############################################################################
  ## Extract runtime inputs from CLI arguments
  ##############################################################################

  files <- read.table(args$infilemap)
  input <- as.data.frame(t(files$V2))
  names(input) <- files$V1
  
  ##############################################################################
  ## Initialization
  ##############################################################################
  report <- newReport("Broad GDAC FireCloud SmokeTest Report")
  
  ##############################################################################
  ## References
  ##############################################################################
  
  ref1 <- newWebCitation("", "Simple gdac-firecloud smoke test",
                         "https://github.com/broadinstitute/gdac-firecloud")
  ref2 <- newWebCitation("", "FireBrowse", "http://firebrowse.org")
  report <- addToReferences(report, ref1, ref2)
  
  ##############################################################################
  ## Introduction
  ##############################################################################
  report <- addToIntroduction(report,
                              newParagraph("Simple report to show some text, ",
                                           "references, as well as an ",
                                           "embedded image and table."))
  
  ##############################################################################
  ## Results
  ##############################################################################

  data <- read.table(input$table, sep="\t", header=TRUE, comment.char='#',
                     quote="", stringsAsFactors=FALSE)
  table <- newTable(data, file=basename(input$table))
  report <- addToResults(report, table)

  plot <- newFigure(basename(input$plot),
                    "Placeholder caption, for this placeholder figure")
  report <- addToResults(report, plot)

  ##############################################################################
  ## Done
  ##############################################################################
  writeReport(report)
}

main(args)
