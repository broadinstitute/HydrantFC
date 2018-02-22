task smoketest_task {
    Boolean package
    String null_file
    String package_name
    String package_archive="${package_name}.zip"
    Int? local_disk_gb
    Int? num_preemptions

    String? inputHeader
    File inputPlot
    String table = "table.txt"
    String document = "document.txt"
    String zipfile = "smoketest_outputs.zip"

    command {
        set -euo pipefail

        # First fabricate a simple output table
        header="${default="Empty: no header provided" inputHeader}"
        echo "# $header"           > ${table}
        echo "Col1	Col2	Col3	Col4" >> ${table}
        echo "1	1	1	1"        >> ${table}
        echo "2	2	2	2"        >> ${table}

        # Now fabricate a simple "document"
        echo "Line1"                         > ${document}
        for i in 2 3 4 5 ; do
            echo "Line$i"                   >> ${document}
        done

        # Pause to simulate that task does not complete nearly instantaneously
        sleep 10

        # Finally, ensure that the input plot is passed through as output
        cp -f ${inputPlot} .

        echo "plot `basename ${inputPlot}`" > filemap.tsv
        echo "table ${table}"               >> filemap.tsv
        echo "document ${document}"         >> filemap.tsv
        zip ${zipfile} *.png *.txt *.tsv

        if ${package}; then
            package.sh \
                -x broad-institute-gdac/\* \
                -x ${zipfile} \
                ${package_name}
        fi
    }

    output {
        File smoketest_pkg="${if package then package_archive else null_file}"
        File outputs = zipfile
    }

    runtime {
        docker : "broadgdac/firecloud-ubuntu:16.04"
        disks : "local-disk ${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "Broad GDAC"
        email : "gdac@broadinstitute.org"
    }
}

task smoketest_report {
    Boolean package
    String null_file
    File package_archive
    String package_name=basename(package_archive)
    Int? local_disk_gb
    Int? num_preemptions

    File files_archive
    String files_archive_name = basename(files_archive)

    command {
        set -euo pipefail
        
        # Outside of the command block, files_archive reverts to the original
        # path, thus any updates done locally aren't passed on. By moving the
        # localized copy into the working directory, and passing the String
        # files_archive_name to the output File results, modifications can be
        # passed along.
        
        mv ${files_archive} .
        unzip ${files_archive_name}
        
        Rscript /src/smokereport.R --infilemap filemap.tsv

        zip -u ${files_archive_name} *.html *.RData
        
        if ${package}; then
            mv ${package_archive} .
            /src/package.sh \
                -x broad-institute-gdac/\* \
                -x ${files_archive_name} \
                ${package_name}
        fi
    }

    output {
        File smoketest_pkg="${if package then package_name else null_file}"
        File results = files_archive_name
    }

    runtime {
        docker : "broadgdac/smoketest_report:1"
        disks : "local-disk ${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "Broad GDAC"
        email : "gdac@broadinstitute.org"
    }
}

workflow smoketest {
    Boolean package
    String null_file="gs://broad-institute-gdac/GDAC_FC_NULL"
    String package_name="smoketest"

    call smoketest_task {
        input: package=package,
               null_file=null_file,
               package_name=package_name
    }

    call smoketest_report {
        input: package=package,
               null_file=null_file,
               package_archive=smoketest_task.smoketest_pkg,
               files_archive=smoketest_task.outputs
    }

    output {
        smoketest_report.smoketest_pkg
        smoketest_report.results
    }
}
