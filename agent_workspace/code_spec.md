# Generated Spec

{
  "task_type": "code",
  "overall_goal": "Develop a secure FastAPI user authentication module supporting JWT-based login and database persistence.",
  "success_criteria": [
    "Login endpoint returns valid JWT token upon successful credential verification.",
    "Password is stored hashed using bcrypt or argon2 in the database.",
    "Protected endpoints reject requests without valid JWT.",
    "Database schema includes User table with unique username/email.",
    "Input validation implemented using Pydantic models.",
    "No sensitive data (passwords, secrets) logged or exposed in responses."
  ],
  "progress_tracking": {
    "current_progress": "Spec initialization and requirement analysis phase.",
    "completed_steps": [],
    "remaining": [
      "Define database models and schema (User table).",
      "Implement password hashing and verification utilities.",
      "Create JWT encoding and decoding functions.",
      "Develop API endpoints (register, login, get_current_user).",
      "Write unit tests for authentication logic.",
      "Add security middleware and dependency injection.",
      "Generate API documentation and usage examples."
    ]
  },
  "process_requirements": [
    "Record all development steps in a progress log.",
    "Ensure code is modular and separable (routes, schemas, models, auth).",
    "Verify compatibility with FastAPI best practices.",
    "Maintain transparency in Thought → Action → Observation flow."
  ],
  "boundaries": {
    "always": [
      "Use environment variables for JWT_SECRET_KEY and DATABASE_URL.",
      "Hash passwords before storing them in the database.",
      "Validate all user inputs using Pydantic models.",
      "Include error handling for invalid credentials and token expiration.",
      "Follow PEP 8 coding standards."
    ],
    "ask_first": [
      "Preferred database backend (SQLite, PostgreSQL, MySQL)?",
      "Specific user fields required beyond username and password (e.g., email, role)?",
      "JWT token expiration time preference?"
    ],
    "never": [
      "Store plain text passwords in the database.",
      "Hardcode secrets or credentials in the source code.",
      "Return password hashes or sensitive user data in API responses.",
      "Execute destructive database operations without confirmation."
    ]
  },
  "self_check_instructions": [
    "Verify that password hashing algorithm is secure (e.g., bcrypt).",
    "Ensure JWT secret is not exposed in client-side code or logs.",
    "Check that database queries use ORM or parameterized statements to prevent SQL injection.",
    "Confirm that protected routes enforce dependency injection for user authentication."
  ],
  "human_in_loop_points": [],
  "additional_notes": "# Code Task Specification\n\n## Objective\nDevelop a secure FastAPI user authentication module supporting JWT-based login and database persistence.\n\n## Success Criteria\n- 代码必须能正常运行且通过基本测试\n- 结构清晰，包含必要注释\n- 遵守安全最佳实践\n\n## Boundaries\n**Always:**\n- 先规划文件结构和接口\n- 生成代码前说明设计决策\n\n**Never:**\n- 直接执行未经测试的代码"
}