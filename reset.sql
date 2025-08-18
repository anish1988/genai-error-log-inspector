ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'root@123Abc';
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root@123Abc';
FLUSH PRIVILEGES;
