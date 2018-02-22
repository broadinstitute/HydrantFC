#! /bin/bash

# This script simplifies use of Cromwell from the CLI, in several ways:
#
#   - captures stdout to log file, so terminal stays clean if no errors occur
#   - on error:
#       . filters WDL execution log to display the most useful content
#       . automatically finds and displays the contents of stderr 
#       . creates soft link to the execution directory, called latest
#
# Assumes color terminal (error content is bracked by RED control sequences)

if [ "$1" = "-x" ] ; then
    # Helpful cli debugging
    set -x
    shift
fi

myDir=`dirname $0`
Options=$myDir/options.json

CromWell=$1
PathToWDL=$2
PathToInputs=$3
shift 3

redmsg()
{
    echo "[38;5;1m${@}[0m"
}

chkfile()
{
    if [ ! -s $1 ] ; then
        redmsg "File missing or empty: $1"
        exit 1
    fi
}

chkfile $CromWell
chkfile $PathToWDL
chkfile $PathToInputs
chkfile $Options

TaskNames=(`egrep "^[       ]*task" $PathToWDL | awk '{print $2}'`)
FlowName=`egrep -m 1 "^[       ]*workflow " $PathToWDL | awk '{print $2}'`
ExecDir=running
DoneDir=latest
LogFile=run-${FlowName}.`date +"%Y_%m_%d__%H_%M_%S"`.log

Command="java -jar $CromWell run -i $PathToInputs -o $Options $PathToWDL"
echo
redmsg "Running cromwell:"
echo "    $Command"

\rm -rf $ExecDir
mkdir $ExecDir
$Command 2>&1 | \
    awk -v FlowName=$FlowName \
        -v TaskNames="${TaskNames[*]}" \
        -v LogFile=$LogFile   \
        -v ExecDir=$ExecDir '

        BEGIN {split(TaskNames, TaskNameAry)}
        # Log workflow output, but let caller know the workflow execution dir
        # and soft link it to ./$ExecDir so long-running jobs can be inspected

        /^.*Workflow[ 	][ 	]*([^ 	 ]*)[ 	][ 	]*submitted.*$/ {
            id = substr($0, index($0, "Workflow") + 8, 999)
            split(id, tokens)
            id = tokens[1]
            PathPrefix="cromwell-executions/"FlowName"/"id
            print "    ExecutionDir(s):"
            for (i=1; i<=length(TaskNameAry); i++) {
                Dir=PathPrefix"/call-"TaskNameAry[i]"/execution/"
                print "        "Dir
                system("ln -s ../"Dir" "ExecDir"/"TaskNameAry[i])
            }
            print "    (linked in ./"ExecDir" during execution, then ./latest)"
        }

        {
            print $0 > LogFile
            next
        }'
Error=$?
echo

# Update "latest finished run" soft link to directory pointed to by $ExecDir
if [ -d $ExecDir ] ; then
    \rm -rf ./$DoneDir
    mv $ExecDir $DoneDir
    LatestMsg="look in ./$DoneDir for artifacts generated during this run"
else
    \rm -rf $ExecDir
fi

if ((!$Error)) ; then
    \rm -f $LogFile
    echo "Success: $LatestMsg"
    exit 0
fi

redmsg "Error: see filtered log below (and stderr, if available)"
sed -e '/^.*\[info\].*$/d'  \
    -e '/^java.lang.*/d'    \
    -e '/^[ 	][ 	]*.*/d' \
    $LogFile | awk '{print "    "$0}'

# Dump the stderr output, too, as a convenience
for task in ${TaskNames[*]} ; do
	StdErr=$DoneDir/$task/stderr
	echo
	if [ -f $StdErr ] ; then
	    redmsg ${StdErr}:
	    awk '{print "    "$0}' $StdErr
	    echo
	fi
done

exit $Error
