# Fighting Connection Pool Exhaustion in Microservices

> Medium draft — tags to add: devops, ai, microservices, postgresql

Connection pool exhaustion can bring down even the most robust microservices architecture.

---

### The Problem: Troubleshooting Connection Pool Exhaustion in Distributed Systems
Connection pool exhaustion is a common issue in distributed systems, where multiple threads or requests compete for a limited number of database connections. This can lead to increased latency, errors, and even system crashes. In a recent production outage, we experienced connection pool exhaustion due to a combination of high traffic and inefficient connection management.

### Technical Breakdown
To understand the root cause of the issue, let's dive into the technical details. Our system uses a Java-based application server, with a connection pool managed by the `java.sql.DriverManager`. The connection pool is configured with a maximum size of 100 connections, and a timeout of 30 seconds.
```java
// Connection pool configuration
DataSource dataSource = DataSourceBuilder.create()
    .driverClassName("com.mysql.cj.jdbc.Driver")
    .url("jdbc:mysql://localhost:3306/mydb")
    .username("myuser")
    .password("mypass")
    .maxTotal(100)
    .maxWaitMillis(30000)
    .build();
```
However, during peak hours, the number of incoming requests exceeds the maximum connection pool size, causing threads to wait for available connections. This leads to increased latency and errors, as threads timeout or are terminated due to lack of resources.

### The Fix / Pattern
To resolve the connection pool exhaustion issue, we implemented the following steps:

1. **Increased connection pool size**: We increased the maximum connection pool size to 200, to accommodate the increased traffic.
```java
// Updated connection pool configuration
DataSource dataSource = DataSourceBuilder.create()
    .driverClassName("com.mysql.cj.jdbc.Driver")
    .url("jdbc:mysql://localhost:3306/mydb")
    .username("myuser")
    .password("mypass")
    .maxTotal(200)
    .maxWaitMillis(30000)
    .build();
```
2. **Implemented connection validation**: We added connection validation to ensure that connections are valid and usable before returning them to the pool.
```java
// Connection validation configuration
dataSource.setValidationQuery("SELECT 1");
dataSource.setTestOnBorrow(true);
```
3. **Optimized database queries**: We optimized database queries to reduce the number of connections required, by using efficient query methods and minimizing the use of transactions.
```java
// Optimized database query example
@Repository
public class MyRepository {
    @Autowired
    private EntityManager entityManager;
    
    public List<MyEntity> findEntities() {
        return entityManager.createQuery("SELECT e FROM MyEntity e", MyEntity.class).getResultList();
    }
}
```
4. **Monitored connection pool metrics**: We monitored connection pool metrics, such as active connections, idle connections, and wait time, to detect potential issues before they occur.
```java
// Connection pool metrics monitoring
@Scheduled(fixedDelay = 10000)
public void monitorConnectionPool() {
    int activeConnections = dataSource.getNumActive();
    int idleConnections = dataSource.getNumIdle();
    long waitTime = dataSource.getWaitTime();
    
    // Log or alert on potential issues
    if (activeConnections > 150 || waitTime > 10000) {
        // Log or alert
    }
}
```
### Key Takeaway
By implementing connection pool optimization, validation, and monitoring, we can prevent connection pool exhaustion and ensure reliable database connectivity in distributed systems, reducing errors and latency by proactively managing connection resources.