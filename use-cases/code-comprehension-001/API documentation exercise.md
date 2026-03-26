@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': 'Missing required field',
                'message': f'{field} is required'
            }), 400

    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'error': 'Username taken',
            'message': 'Username is already in use'
        }), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'error': 'Email exists',
            'message': 'An account with this email already exists'
        }), 409

    # Validate email format
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", data['email']):
        return jsonify({
            'error': 'Invalid email',
            'message': 'Please provide a valid email address'
        }), 400

    # Validate password strength
    if len(data['password']) < 8:
        return jsonify({
            'error': 'Weak password',
            'message': 'Password must be at least 8 characters long'
        }), 400

    # Create new user
    try:
        # Hash password
        password_hash = generate_password_hash(data['password'])

        # Create user object
        new_user = User(
            username=data['username'],
            email=data['email'].lower(),
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            role='user'
        )

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        # Generate confirmation token
        confirmation_token = generate_confirmation_token(new_user.id)

        # Send confirmation email
        try:
            send_confirmation_email(new_user.email, confirmation_token)
        except Exception as e:
            # Log email error but continue
            app.logger.error(f"Failed to send confirmation email: {str(e)}")

        # Create response without password
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'created_at': new_user.created_at.isoformat(),
            'role': new_user.role
        }

        return jsonify({
            'message': 'User registered successfully',
            'user': user_data
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering user: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to register user'
        }), 500


# Prompt 1
Here is comprehensive API documentation for your user registration endpoint:

---

## POST `/api/users/register`

### 1. Description

Registers a new user account.  
Validates required fields, checks for unique username/email, enforces password strength, and sends a confirmation email.  
Returns the created user (without password) on success.

---

### 2. Request Parameters

- **Body (JSON):**
  - `username` (string, required): Desired username (must be unique)
  - `email` (string, required): User’s email address (must be unique, valid format)
  - `password` (string, required): User’s password (minimum 8 characters)

_No path or query parameters._

---

### 3. Response Format

- **Success (201 Created):**
  ```json
  {
    "message": "User registered successfully",
    "user": {
      "id": 123,
      "username": "johndoe",
      "email": "johndoe@example.com",
      "created_at": "2026-03-26T12:34:56.789Z",
      "role": "user"
    }
  }
  ```

- **Error (various codes):**
  ```json
  {
    "error": "Error type",
    "message": "Human-readable message"
  }
  ```

---

### 4. Authentication

- **None required.**  
  This endpoint is public for new user registration.

---

### 5. Potential Error Responses

| Status | Error         | Message                                 |
|--------|--------------|-----------------------------------------|
| 400    | Missing required field | `<field> is required`         |
| 400    | Invalid email | `Please provide a valid email address`  |
| 400    | Weak password | `Password must be at least 8 characters long` |
| 409    | Username taken| `Username is already in use`            |
| 409    | Email exists  | `An account with this email already exists` |
| 500    | Server error  | `Failed to register user`               |

---

### 6. Example Requests & Responses

**Example 1: Successful Registration**

_Request:_
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "securePass123"
}
```
_Response (201):_
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-03-26T12:34:56.789Z",
    "role": "user"
  }
}
```

**Example 2: Username Already Taken**

_Request:_
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice2@example.com",
  "password": "securePass123"
}
```
_Response (409):_
```json
{
  "error": "Username taken",
  "message": "Username is already in use"
}
```

---

### 7. Rate Limiting & Special Considerations

- **Rate Limiting:** Not specified in code, but recommended to prevent abuse (e.g., max X registrations per IP/hour).
- **Email Confirmation:** Registration triggers a confirmation email; failure to send is logged but does not block registration.
- **Password Storage:** Passwords are securely hashed before storage.
- **Case Sensitivity:** Emails are stored in lowercase; username uniqueness is case-sensitive.
- **Atomicity:** If any error occurs during user creation, the database transaction is rolled back.

---

**Note:**  
Always use HTTPS to protect sensitive data in transit.  
Consider adding CAPTCHA or email verification to prevent automated abuse.

# Prompt 2

```yaml
openapi: 3.0.3
info:
  title: User Registration API
  description: >
    API for registering new user accounts. Validates required fields,
    enforces unique username/email, enforces password strength, and
    sends a confirmation email. Returns the created user (without password)
    on success.
  version: 1.0.0

servers:
  - url: https://your-domain.com
    description: Production server

paths:
  /api/users/register:
    post:
      summary: Register a new user account
      description: >
        Creates a new user account after validating required fields,
        checking for unique username and email, enforcing password strength
        (minimum 8 characters), and sending a confirmation email.
        The password is never returned in the response.
      operationId: registerUser
      tags:
        - Users
      security: []  # No authentication required

      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterRequest'
            examples:
              successful_registration:
                summary: Valid registration payload
                value:
                  username: alice
                  email: alice@example.com
                  password: securePass123
              duplicate_username:
                summary: Already-taken username
                value:
                  username: alice
                  email: alice2@example.com
                  password: securePass123

      responses:
        '201':
          description: User registered successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegisterSuccess'
              example:
                message: User registered successfully
                user:
                  id: 42
                  username: alice
                  email: alice@example.com
                  created_at: "2026-03-26T12:34:56.789Z"
                  role: user

        '400':
          description: Validation error (missing field, invalid email, or weak password)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                missing_field:
                  summary: Required field absent
                  value:
                    error: Missing required field
                    message: username is required
                invalid_email:
                  summary: Malformed email address
                  value:
                    error: Invalid email
                    message: Please provide a valid email address
                weak_password:
                  summary: Password too short
                  value:
                    error: Weak password
                    message: Password must be at least 8 characters long

        '409':
          description: Conflict — username or email is already in use
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                username_taken:
                  summary: Username already registered
                  value:
                    error: Username taken
                    message: Username is already in use
                email_exists:
                  summary: Email already registered
                  value:
                    error: Email exists
                    message: An account with this email already exists

        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              example:
                error: Server error
                message: Failed to register user

components:
  schemas:

    RegisterRequest:
      type: object
      required:
        - username
        - email
        - password
      properties:
        username:
          type: string
          description: Desired username (must be unique; case-sensitive)
          example: alice
        email:
          type: string
          format: email
          description: >
            User's email address (must be unique; stored in lowercase).
            Must match the pattern user@domain.tld.
          example: alice@example.com
        password:
          type: string
          format: password
          minLength: 8
          description: Account password (minimum 8 characters; stored as a hash)
          example: securePass123

    RegisterSuccess:
      type: object
      properties:
        message:
          type: string
          example: User registered successfully
        user:
          $ref: '#/components/schemas/UserResponse'

    UserResponse:
      type: object
      description: Public user object (password excluded)
      properties:
        id:
          type: integer
          description: Auto-generated unique user identifier
          example: 42
        username:
          type: string
          example: alice
        email:
          type: string
          format: email
          example: alice@example.com
        created_at:
          type: string
          format: date-time
          description: ISO 8601 timestamp of account creation (UTC)
          example: "2026-03-26T12:34:56.789Z"
        role:
          type: string
          description: User role assigned at registration
          enum:
            - user
            - admin
          example: user

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Short machine-readable error type
          example: Username taken
        message:
          type: string
          description: Human-readable explanation of the error
          example: Username is already in use
```

# Prompt 3

---

# Developer Guide: User Registration Endpoint

**Endpoint:** `POST /api/users/register`  
**Audience:** Junior Developers  
**Base URL:** `https://your-domain.com`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Formatting Requests](#2-formatting-requests)
3. [Handling and Interpreting Responses](#3-handling-and-interpreting-responses)
4. [Common Errors and How to Handle Them](#4-common-errors-and-how-to-handle-them)
5. [Example Code](#5-example-code)

---

## 1. Authentication

The `/api/users/register` endpoint is **publicly accessible** and does **not** require any authentication token, API key, or session credential. Any client may call this endpoint without prior authorisation.

However, the following security practices are strongly recommended:

- **Always use HTTPS.** Transmitting credentials over plain HTTP exposes passwords to interception. Ensure your base URL begins with `https://`.
- **Do not reuse passwords.** Instruct users to choose passwords that are unique to this service.
- **Consider rate limiting on the client side.** Although the server may enforce its own rate limits, avoid sending bursts of registration requests from your application.

---

## 2. Formatting Requests

### Method and URL

```
POST https://your-domain.com/api/users/register
```

### Required Headers

| Header         | Value              |
|----------------|--------------------|
| `Content-Type` | `application/json` |

### Request Body

The request body must be a valid JSON object containing the following fields:

| Field      | Type   | Required | Constraints                              |
|------------|--------|----------|------------------------------------------|
| `username` | string | Yes      | Must be unique (case-sensitive)          |
| `email`    | string | Yes      | Must be a valid email; must be unique    |
| `password` | string | Yes      | Minimum 8 characters                    |

**Important notes:**

- All three fields must be present. Omitting any field will result in a `400` error.
- The `email` field is stored in lowercase regardless of the case supplied. Ensure your application normalises email display accordingly.
- The `password` is **never** stored in plain text and is **never** returned in any response.

**Example request body:**

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "securePass123"
}
```

---

## 3. Handling and Interpreting Responses

### Successful Response — `201 Created`

A `201` status code indicates the account was created successfully. The response body will contain a confirmation message and the new user's public profile.

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-03-26T12:34:56.789Z",
    "role": "user"
  }
}
```

**Fields returned:**

| Field        | Type    | Description                                      |
|--------------|---------|--------------------------------------------------|
| `id`         | integer | Unique identifier for the newly created user     |
| `username`   | string  | The username as provided in the request          |
| `email`      | string  | The email stored in lowercase                    |
| `created_at` | string  | ISO 8601 UTC timestamp of account creation       |
| `role`       | string  | Always `"user"` for self-registered accounts     |

> **Note:** A confirmation email is dispatched asynchronously after registration. Failure to send the email is logged on the server but does **not** prevent the account from being created or affect the `201` response.

### Error Response Structure

All error responses share the same JSON shape:

```json
{
  "error": "Short machine-readable label",
  "message": "Human-readable explanation"
}
```

Use the HTTP status code to branch your error-handling logic first, then use the `error` field for more granular messaging to the user.

---

## 4. Common Errors and How to Handle Them

| Status | `error` value           | Cause                                            | Recommended Action                                                 |
|--------|-------------------------|--------------------------------------------------|--------------------------------------------------------------------|
| `400`  | `Missing required field`| A required field (`username`, `email`, or `password`) was not included in the request body | Validate all fields client-side before submitting the request      |
| `400`  | `Invalid email`         | The supplied email does not match a valid format | Validate email format with a regex or library before submission    |
| `400`  | `Weak password`         | The password is fewer than 8 characters          | Enforce the minimum length constraint in your form or UI           |
| `409`  | `Username taken`        | The username is already registered               | Prompt the user to choose a different username                     |
| `409`  | `Email exists`          | The email address is already associated with an account | Inform the user and suggest using the login or password-reset flow |
| `500`  | `Server error`          | An unexpected server-side failure occurred       | Display a generic error message; retry the request after a delay   |

### Client-Side Validation Checklist

Validating inputs before sending the request reduces unnecessary network round-trips:

- [ ] `username` field is not empty.
- [ ] `email` field matches a valid email pattern (e.g., `user@domain.tld`).
- [ ] `password` field is at least 8 characters long.

---

## 5. Example Code

### Python (using `requests`)

```python
import requests

BASE_URL = "https://your-domain.com"

def register_user(username: str, email: str, password: str) -> dict:
    url = f"{BASE_URL}/api/users/register"
    payload = {
        "username": username,
        "email": email,
        "password": password,
    }

    response = requests.post(url, json=payload)

    if response.status_code == 201:
        print("Registration successful.")
        return response.json()["user"]

    # Handle known error codes
    error_body = response.json()
    if response.status_code == 400:
        raise ValueError(f"Validation error: {error_body['message']}")
    elif response.status_code == 409:
        raise ValueError(f"Conflict: {error_body['message']}")
    else:
        raise RuntimeError(f"Unexpected error ({response.status_code}): {error_body.get('message')}")


# Usage
try:
    user = register_user("alice", "alice@example.com", "securePass123")
    print(f"Created user: {user['id']} — {user['username']}")
except ValueError as e:
    print(f"Registration failed: {e}")
except RuntimeError as e:
    print(f"Server error: {e}")
```

---

### JavaScript (using `fetch`, browser or Node.js 18+)

```javascript
const BASE_URL = "https://your-domain.com";

async function registerUser(username, email, password) {
  const response = await fetch(`${BASE_URL}/api/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });

  const data = await response.json();

  if (response.status === 201) {
    console.log("Registration successful:", data.user);
    return data.user;
  }

  // Map status codes to meaningful errors
  if (response.status === 400 || response.status === 409) {
    throw new Error(data.message);
  }

  throw new Error(`Unexpected server error: ${response.status}`);
}

// Usage
registerUser("alice", "alice@example.com", "securePass123")
  .then((user) => console.log(`Created user ID: ${user.id}`))
  .catch((err) => console.error("Registration failed:", err.message));
```

---

### cURL (command line)

**Successful registration:**

```bash
curl -X POST https://your-domain.com/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "securePass123"}'
```

**Expected output (201):**

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-03-26T12:34:56.789Z",
    "role": "user"
  }
}
```

---

## Summary

| Step | Action |
|------|--------|
| 1 | No authentication token required — call the endpoint directly over HTTPS |
| 2 | Send a `POST` request with `Content-Type: application/json` and a body containing `username`, `email`, and `password` |
| 3 | On `201`, read the returned `user` object for the new account details |
| 4 | On `4xx`, inspect the `error` and `message` fields and surface a meaningful message to the user |
| 5 | On `5xx`, display a generic failure message and allow the user to retry |

