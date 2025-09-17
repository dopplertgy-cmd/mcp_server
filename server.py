#!/usr/bin/env python3
"""
MCP Server for ChatGPT with Sample Functions
Provides file operations, text processing, calculations, web scraping, and AI capabilities.
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional
from fastmcp import FastMCP

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

# Initialize FastMCP server
mcp = FastMCP("ChatGPT MCP Server")

# OpenAI client initialization
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SERVER_API_KEY = os.environ.get("SERVER_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")

# =============================================================================
# DATABASE FUNCTIONS - EMPLOYEE RECORDS
# =============================================================================


def get_db_connection():
    """Get database connection"""
    if not DATABASE_URL:
        raise Exception("Database not configured")
    return psycopg2.connect(DATABASE_URL)


def init_employees_table():
    """Initialize employees table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create employees table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        department VARCHAR(100),
                        position VARCHAR(100),
                        salary DECIMAL(10,2),
                        hire_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        phone_number TEXT,
                        ssn TEXT,
                        address TEXT 
                    )
                """)

                # Check if table is empty and add sample data
                cur.execute("SELECT COUNT(*) FROM employees")
                count = cur.fetchone()[0]

                if count == 0:
                    # Add sample employees
                    sample_employees = [
                        (
                            'John',
                            'Doe',
                            'john.doe@company.com',
                            'Engineering',
                            'Senior Developer',
                            95000,
                            '2022-01-15',
                            '4545668595',
                            '265466164',
                            '526 North Lane, Springfield, IL 62705',
                        ),
                        (
                            'Jane',
                            'Smith',
                            'jane.smith@company.com',
                            'Marketing',
                            'Marketing Manager',
                            75000,
                            '2021-06-01',
                            '2656859463',
                            '329548765',
                            '6487 South Lane, Springfield, IL 62704',
                        ),
                        ('Mike', 'Johnson', 'mike.johnson@company.com',
                         'Sales', 'Sales Representative', 65000, '2023-03-10',
                         '2656859463', '2253365487',
                         '2658 West Lane, Springfield, IL 62701'),
                    ]

                    cur.executemany(
                        """
                        INSERT INTO employees (first_name, last_name, email, department, position, salary, hire_date, phone_number, ssn, address)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, sample_employees)

                conn.commit()
        return "✅ Employees table initialized successfully"
    except Exception as e:
        return f"❌ Error initializing employees table: {str(e)}"


@mcp.tool()
def get_employee_records(employee_id: Optional[int] = None) -> str:
    """Get employee records. If employee_id is provided, get that specific employee; otherwise return all employees."""
    try:
        # Initialize table if needed
        init_result = init_employees_table()
        if "Error" in init_result:
            return init_result

        with get_db_connection() as conn:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if employee_id is not None:
                    # Get specific employee
                    cur.execute(
                        """
                        SELECT *
                        FROM employees 
                        WHERE id = %s
                    """, (employee_id, ))
                    employee = cur.fetchone()

                    if not employee:
                        return f"❌ Employee with ID {employee_id} not found"

                    result = f"""📋 Employee Record - ID: {employee['id']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {employee['first_name']} {employee['last_name']}
✉️  Email: {employee['email']}
🏢 Department: {employee['department']}
💼 Position: {employee['position']}
💰 Salary: ${employee['salary']:,.2f}
Address: {employee['address']}
Phone Number: {employee['phone_number']}
SSN: {employee['ssn']}
📅 Hire Date: {employee['hire_date']}
🕒 Record Created: {employee['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"""

                else:
                    # Get all employees
                    cur.execute("""
                        SELECT *
                        FROM employees 
                        ORDER BY id
                    """)
                    employees = cur.fetchall()

                    if not employees:
                        return "❌ No employee records found"

                    result = f"📋 All Employee Records ({len(employees)} employees)\n"
                    result += "=" * 60 + "\n\n"

                    for emp in employees:
                        result += f"👤 ID: {emp['id']} | {emp['first_name']} {emp['last_name']}\n"
                        result += f"   ✉️  {emp['email']}\n"
                        result += f"   🏢 {emp['department']} - {emp['position']}\n"
                        result += f"   🏠 {emp['address']}\n"
                        result += f"   📞 {emp['phone_number']}\n"
                        result += f"   🔒 {emp['ssn']}\n"
                        result += f"   💰 ${emp['salary']:,.2f} | 📅 Hired: {emp['hire_date']}\n\n"

        return result

    except Exception as e:
        if "Database not configured" in str(e):
            return "❌ Database not available. Employee records require database setup."
        return f"❌ Error retrieving employee records: {str(e)}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


@mcp.tool()
def get_mcp_info() -> str:
    """Get information about this MCP server and available functions"""
    info = """🚀 ChatGPT MCP Server Information
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


👥 Employee Records (database):
   • get_employee_records(employee_id) - Get all employees or specific employee by ID

🔧 Utility:
   • get_mcp_info() - This information
   • get_server_data() - Get the server's data
   • set_server_data(key) - Set the server's data'

OpenAI Integration: """ + ("✅ Configured"
                           if openai_client else "❌ Not configured") + f"""
Database Integration: """ + ("✅ Configured"
                             if DATABASE_URL else "❌ Not configured")

    return info


@mcp.tool()
def get_server_data() -> dict:
    """Get the server data"""
    return {
        "name": "new_mcp_server",
        "api_key": SERVER_API_KEY,
        "creation_date": "08/07/2025 12:00:00",
        "version": "1.0.0",
    }


@mcp.tool()
def set_server_data(api_key: str) -> str:
    """Set the server API key"""
    os.environ["SERVER_API_KEY"] = api_key
    return "✅ Server API key set successfully"


if __name__ == "__main__":
    import sys
    print("🚀 Starting ChatGPT MCP Server...")
    print("Available functions:",
          len([f for f in dir(mcp) if not f.startswith('_')]))

    if openai_client:
        print("✅ OpenAI integration configured")
    else:
        print(
            "⚠️  OpenAI API key not found - AI functions will be unavailable")

    # Check command line arguments for transport mode
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        print("🌐 Starting HTTP server on port 5000...")
        print("📡 Public URL will be available shortly...")
        mcp.run(transport="http", host="0.0.0.0", port=5000, path="/mcp")
    else:
        print("📡 Starting with STDIO transport...")
        mcp.run()
