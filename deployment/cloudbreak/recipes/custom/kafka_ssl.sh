#!/bin/sh

#Certificates util; for details, check kafka_ssl.txt. Protect this file properly - a master password for all keyrings is hardcoded.

CERTS_DIR=/home/kafka/certs
VALIDITY=365
MASTERPASS=masterpass
DNAME="CN=J.DeBree,OU=IT,O=CowManagerB.V.,L=Harmelen,ST=Utrecht,C=NL"

mkdir -p $CERTS_DIR

keytool -keystore $CERTS_DIR/kafka.server.keystore.jks -alias localhost -validity $VALIDITY -genkey -storepass $MASTERPASS -keypass $MASTERPASS -dname $DNAME -noprompt

openssl req -new -x509 -keyout $CERTS_DIR/ca-key -out $CERTS_DIR/ca-cert -days $VALIDITY -passout pass:$MASTERPASS -subj /$DNAME
keytool -keystore $CERTS_DIR/kafka.client.truststore.jks -alias CARoot -import -file $CERTS_DIR/ca-cert -storepass $MASTERPASS -keypass $MASTERPASS -noprompt
keytool -keystore $CERTS_DIR/kafka.server.truststore.jks -alias CARoot -import -file $CERTS_DIR/ca-cert -storepass $MASTERPASS -keypass $MASTERPASS -noprompt

keytool -keystore $CERTS_DIR/kafka.server.keystore.jks -alias localhost -certreq -file $CERTS_DIR/cert-file -storepass $MASTERPASS -keypass $MASTERPASS -noprompt

openssl x509 -req -CA $CERTS_DIR/ca-cert -CAkey $CERTS_DIR/ca-key -in $CERTS_DIR/cert-file -out $CERTS_DIR/cert-signed -days $VALIDITY -CAcreateserial -passin pass:$MASTERPASS

keytool -keystore $CERTS_DIR/kafka.server.keystore.jks -alias CARoot -import -file $CERTS_DIR/ca-cert -storepass $MASTERPASS -keypass $MASTERPASS -noprompt
keytool -keystore $CERTS_DIR/kafka.server.keystore.jks -alias localhost -import -file $CERTS_DIR/cert-signed -storepass $MASTERPASS -keypass $MASTERPASS -noprompt

keytool -keystore $CERTS_DIR/kafka.client.keystore.jks -alias localhost -validity $VALIDITY -genkey -storepass $MASTERPASS -keypass $MASTERPASS -dname $DNAME -noprompt
keytool -importkeystore -srckeystore $CERTS_DIR/kafka.client.keystore.jks -destkeystore $CERTS_DIR/kafka.client.keystore.p12 -deststoretype PKCS12 -storepass $MASTERPASS -keypass $MASTERPASS -srcstorepass $MASTERPASS -noprompt
openssl pkcs12 -nokeys -in $CERTS_DIR/kafka.client.keystore.p12 -out $CERTS_DIR/cert-file.pem -passin pass:$MASTERPASS
openssl pkcs12 -nocerts -nodes -in $CERTS_DIR/kafka.client.keystore.p12 -out $CERTS_DIR/client-keyfile.key -passin pass:masterpass
