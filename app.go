package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/go-sql-driver/mysql"
)

// 定义用户结构体，对应数据库表结构
type User struct {
	ID   int
	Name string
	Age  int
}

func main() {
	dsn := "root:root@tcp(127.0.0.1:3306)/test_db?charset=utf8mb4&parseTime=True&loc=Local"
	// 2. 连接MySQL
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("连接数据库失败：", err)
	}
	defer db.Close() // 程序结束前关闭连接

	// 验证连接是否有效
	if err := db.Ping(); err != nil {
		log.Fatal("数据库连接无效：", err)
	}
	fmt.Println("数据库连接成功！")

	// 3. 先创建用户表（如果不存在）
	createTableSQL := `
	CREATE TABLE IF NOT EXISTS users (
		id INT AUTO_INCREMENT PRIMARY KEY,
		name VARCHAR(50) NOT NULL,
		age INT
	);`
	_, err = db.Exec(createTableSQL)
	if err != nil {
		log.Fatal("创建表失败：", err)
	}
	fmt.Println("表创建/验证成功！")

	// ---------------------- 增（插入数据）----------------------
	insertSQL := "INSERT INTO users (name, age) VALUES (?, ?)"
	result, err := db.Exec(insertSQL, "张三", 25)
	if err != nil {
		log.Fatal("插入数据失败：", err)
	}
	lastID, _ := result.LastInsertId()
	fmt.Printf("插入成功，新用户ID: %d\n", lastID)

	// ---------------------- 查（查询数据）----------------------
	querySQL := "SELECT id, name, age FROM users WHERE id = ?"
	var user User
	err = db.QueryRow(querySQL, lastID).Scan(&user.ID, &user.Name, &user.Age)
	if err != nil {
		log.Fatal("查询失败：", err)
	}
	fmt.Printf("查询结果: %+v\n", user)

	// ---------------------- 改（更新数据）----------------------
	updateSQL := "UPDATE users SET age = ? WHERE id = ?"
	_, err = db.Exec(updateSQL, 26, lastID)
	if err != nil {
		log.Fatal("更新失败：", err)
	}
	fmt.Println("更新成功！")

	// ---------------------- 删（删除数据）----------------------
	deleteSQL := "DELETE FROM users WHERE id = ?"
	_, err = db.Exec(deleteSQL, lastID)
	if err != nil {
		log.Fatal("删除失败：", err)
	}
	fmt.Println("删除成功！")

	fmt.Println("所有操作执行完毕！")
}
