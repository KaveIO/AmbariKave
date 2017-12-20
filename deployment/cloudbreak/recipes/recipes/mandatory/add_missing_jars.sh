#!/bin/sh
#this is a post recipe!
libdir=/usr/hdp/2.6.1.0-129/hadoop
dest=/var/lib/ambari-server/resources/views/work
for view in $(ls $dest); do
    cp $libdir/hadoop-azure-datalake* $libdir/azure-data-lake-store-sdk* "$dest/$view/WEB-INF/lib/"
done

