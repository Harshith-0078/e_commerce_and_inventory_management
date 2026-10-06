"""
Nexus Peripherals - Database Connection & Configuration Manager
Provides centralized MySQL 8.0 connection lifecycle handling, cursor management,
and schema initialization routines for the BACSE202 DBMS Project.
"""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator, Tuple

try:
    import mysql.connector
    from mysql.connector import errorcode, MySQLConnection
    from mysql.connector.cursor import MySQLCursorDict, MySQLCursor
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    mysql = None  # type: ignore
    errorcode = None  # type: ignore
    MySQLConnection = Any  # type: ignore
    MySQLCursorDict = Any  # type: ignore
    MySQLCursor = Any  # type: ignore
    HAS_MYSQL_CONNECTOR = False

# Default database connection configuration
# Can be overridden via environment variables or explicitly passed
DEFAULT_CONFIG: Dict[str, Any] = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "H@r$#!th2007"),
    "database": os.getenv("DB_NAME", "nexus_peripherals"),
    "charset": "utf8mb4",
    "use_unicode": True,
}


def get_db_config(custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge default database configuration with any user-supplied overrides.
    """
    config = DEFAULT_CONFIG.copy()
    if custom_config:
        config.update({k: v for k, v in custom_config.items() if v is not None})
    return config


def get_db_connection(
    custom_config: Optional[Dict[str, Any]] = None,
    autocommit: bool = False,
    include_database: bool = True
) -> MySQLConnection:
    """
    Establish and return an active MySQL database connection.
    
    :param custom_config: Dictionary with host, user, password, database, port.
    :param autocommit: Whether autocommit is enabled (False recommended for ACID transactions).
    :param include_database: Set to False when connecting to create the database if missing.
    :return: Active MySQLConnection instance.
    :raises ConnectionError: If mysql-connector-python is missing or connection fails.
    """
    if not HAS_MYSQL_CONNECTOR:
        raise ConnectionError("mysql-connector-python is not installed. Please run: pip install -r requirements.txt")

    config = get_db_config(custom_config)
    conn_params = config.copy()
    if not include_database:
        conn_params.pop("database", None)

    try:
        connection = mysql.connector.connect(**conn_params)
        connection.autocommit = autocommit
        return connection
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise ConnectionError("Access denied: Invalid MySQL username or password.") from err
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            raise ConnectionError(f"Database '{config.get('database')}' does not exist.") from err
        else:
            raise ConnectionError(f"MySQL Connection Error [{err.errno}]: {err.msg}") from err


@contextmanager
def get_db_cursor(
    connection: Optional[MySQLConnection] = None,
    custom_config: Optional[Dict[str, Any]] = None,
    dictionary: bool = True,
    autocommit: bool = False
) -> Generator[Tuple[MySQLConnection, Any], None, None]:
    """
    Context manager that yields (connection, cursor) and ensures proper resource cleanup.
    
    Example:
        with get_db_cursor() as (conn, cur):
            cur.execute("SELECT * FROM PRODUCT")
            results = cur.fetchall()
    """
    conn = connection
    owns_connection = False
    if conn is None:
        conn = get_db_connection(custom_config=custom_config, autocommit=autocommit)
        owns_connection = True

    cur = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cur
    finally:
        cur.close()
        if owns_connection:
            conn.close()


def test_connection(custom_config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Test connectivity to the MySQL server and verify database availability.
    
    :return: (is_successful, status_message)
    """
    try:
        conn = get_db_connection(custom_config=custom_config)
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE();")
        version, current_db = cur.fetchone()
        cur.close()
        conn.close()
        return True, f"Successfully connected to MySQL {version} (DB: {current_db})"
    except Exception as e:
        return False, str(e)


def execute_sql_file(sql_file_path: str, custom_config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Parse and execute multi-statement SQL script file (e.g., schema or seed scripts).
    Properly handles DELIMITER directives and multi-line statements.
    """
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found at: {sql_file_path}")

    conn = get_db_connection(custom_config=custom_config, include_database=False)
    cur = conn.cursor()

    try:
        with open(sql_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Handle DELIMITER blocks or standard semicolon-delimited scripts
        statements = []
        current_delimiter = ";"
        current_stmt = []

        lines = content.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("DELIMITER"):
                parts = stripped.split()
                if len(parts) > 1:
                    current_delimiter = parts[1]
                continue

            if not stripped or stripped.startswith("--") or stripped.startswith("/*"):
                continue

            current_stmt.append(line)
            if stripped.endswith(current_delimiter):
                statement_str = "\n".join(current_stmt).rstrip()
                if statement_str.endswith(current_delimiter):
                    statement_str = statement_str[:-len(current_delimiter)].strip()
                if statement_str:
                    statements.append(statement_str)
                current_stmt = []

        if current_stmt:
            remaining = "\n".join(current_stmt).strip()
            if remaining:
                statements.append(remaining)

        for stmt in statements:
            if stmt.strip():
                cur.execute(stmt)

        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def initialize_schema_and_seed(sql_dir_path: str, custom_config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Runs 01_schema.sql, 02_seed_data.sql, and 03_procedures_views.sql in sequence.
    """
    scripts = ["01_schema.sql", "02_seed_data.sql", "03_procedures_views.sql"]
    try:
        for script_name in scripts:
            full_path = os.path.join(sql_dir_path, script_name)
            execute_sql_file(full_path, custom_config=custom_config)
        return True, "Database schema, seed data, and views initialized successfully."
    except Exception as e:
        return False, f"Failed during execution: {str(e)}"
