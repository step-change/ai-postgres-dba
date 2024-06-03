# ai-postgres-dba

Sample app to demonstrate how to build an AI-powered "DBA" to inspect Postgres databases and suggest improvements.

Uses lints from the awesome [splinter](https://github.com/supabase/splinter) project. Try dropping your own in!

## Installation

This project uses [poetry](https://github.com/python-poetry/poetry) to manage a Python virtual environment.

Run `poetry install`.

## Get a Postgres DB

Set up an account at https://timescale.com and create a service.

## Load sample data

We can create some sample tables and load 2M rows from open data sets in the [datablist/sample-csv-files](https://github.com/datablist/sample-csv-files?tab=readme-ov-file) project.

First download the CSV file containing 2M rows of customer data from https://drive.google.com/uc?id=1IXQDp8Um3d-o7ysZLxkDyuvFj9gtlxqz&export=download

Next connect to your postgres database using `psql`, providing your connection string and credentials.

Once you are connected via `psql`, create the tables and indexes with the following SQL statements:

```sql
CREATE TABLE customers (
index SERIAL PRIMARY KEY,
customer_id VARCHAR(255) UNIQUE,
first_name VARCHAR(255),
last_name VARCHAR(255),
company VARCHAR(255),
city VARCHAR(255),
country VARCHAR(255),
phone_1 VARCHAR(255),
phone_2 VARCHAR(255),
email VARCHAR(255),
subscription_date DATE,
website VARCHAR(255)
);

-- Indexes on important fields
CREATE INDEX idx_customer_id ON customers(customer_id);
CREATE INDEX idx_last_name ON customers(last_name);
CREATE INDEX idx_city ON customers(city);
```

Now the schema has been created, load the customers data into table via `psql` shell - making sure to provide the path to the CSV file on your local machine:

```sql
\COPY customers(index, customer_id, first_name, last_name, company, city, country, phone_1, phone_2, email, subscription_date, website)
FROM '/path/to/your/file.csv'
WITH (FORMAT csv, HEADER true);
```

Done! You should see a count of 2,000,000 rows in your `customers` table.

```shell
tsdb=> select count(\*) from customers;
count

---

2000000
(1 row)
```

## Running

You need to set the following environment variables:

- `OPENAI_API_KEY` - get one at https://openai.com
- `PG_DB_URI` - connection string for your Postgres database. Get one at https://timescale.com.

Start the program with `poetry`:

```shell
poetry run ./main.py
```

## Example output

### Analysis of Unused Indexes in PostgreSQL Database

#### Overview of the Query

The provided SQL query is designed to identify indexes in a PostgreSQL database that have never been used. This can help in identifying potential candidates for removal, which might improve database performance and reduce storage costs.

#### Key Elements of the Query

1. **Source Tables and Joins**:

   - `pg_stat_user_indexes (psui)`: Contains statistics about user-defined indexes.
   - `pg_index (pi)`: Contains information about indexes.
   - `pg_depend (dep)`: Contains dependency information to exclude tables owned by extensions.

2. **Conditions**:

   - `psui.idx_scan = 0`: Index has never been scanned.
   - `NOT pi.indisunique`: The index is not unique.
   - `NOT pi.indisprimary`: The index is not a primary key.
   - `dep.objid IS NULL`: Exclude tables owned by extensions.
   - `psui.schemaname NOT IN (...)`: Exclude specific schemas that are likely system or extension schemas.

3. **Output Information**:
   - `name`, `level`, `facing`, `categories`, `description`, `detail`, `remediation`, `metadata`, `cache_key`: Various fields to describe the unused index and provide context and remediation information.

#### Result Analysis

The query result indicates two indexes that have never been used:

1. **Index `idx_customer_id` on table `public.customers`**:

   - **Schema**: `public`
   - **Table**: `customers`
   - **Index**: `idx_customer_id`
   - **Detail**: The index `idx_customer_id` on the `customers` table in the `public` schema has never been used.
   - **Remediation**: Refer to the recommendations provided below for more details on handling unused indexes.

2. **Index `idx_city` on table `public.customers`**:
   - **Schema**: `public`
   - **Table**: `customers`
   - **Index**: `idx_city`
   - **Detail**: The index `idx_city` on the `customers` table in the `public` schema has never been used.
   - **Remediation**: Refer to the recommendations provided below more details on handling unused indexes.

#### Recommendations

1. **Review Indexes**:

   - Verify the necessity of the identified indexes (`idx_customer_id` and `idx_city`). If these indexes are not required for query performance or referential integrity, consider removing them.

2. **Statistics Update**:

   - Ensure that PostgreSQL statistics are up-to-date by running `ANALYZE` on the database. This can help in better query planning and accurate index usage statistics.

3. **Monitor Index Usage**:

   - Continue to monitor index usage over a longer period to confirm that these indexes remain unused. Sometimes, certain indexes may only be used during specific operations or periods.

4. **Storage Considerations**:

   - Removing unused indexes can free up storage space and potentially improve write performance. However, before dropping any indexes, ensure that they are not needed for any specific queries or application logic.

5. **Backup and Documentation**:

   - Document the indexes and their usage statistics before making any changes. Also, consider backing up the database or relevant schema before dropping indexes.

6. **Consult Application Team**:
   - Discuss with the application development team to confirm that these indexes are not planned for future use.

By following these steps, you can ensure that your database remains optimized and that unnecessary indexes are safely removed, improving overall performance.
