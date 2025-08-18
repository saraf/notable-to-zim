---
title: API Access for Redmine
created: '2025-07-04T09:38:07.826Z'
modified: '2025-07-04T09:38:31.306Z'
---

# API Access for Redmine
Created on: 2025-07-04T15:08:31

To start using the Redmine API after enabling it in settings, follow these steps:

### 1. **Get Your API Key**
   - Go to your Redmine account:  
     **User Profile → My Account → API access key** (in the right-hand menu).
   - Generate or copy your unique API key (a long alphanumeric string).  
     ![Redmine API key location](https://www.redmine.org/attachments/download/29108/my-account-api-key.png)

---

### 2. **Authenticate API Requests**
Use the API key in **HTTP headers** for all requests (recommended):  
```http
GET /issues.json HTTP/1.1
Host: your-redmine-url.com
X-Redmine-API-Key: YOUR_API_KEY_HERE
```

**Alternative** (less secure): Append `?key=YOUR_API_KEY` to the URL.

---

### 3. **Test API Access**
Use **cURL** or tools like Postman to verify connectivity.  
**Example (list issues):**
```bash
curl -H "X-Redmine-API-Key: YOUR_API_KEY" https://your-redmine-url.com/issues.json
```

**Successful response:**  
```json
{
  "issues": [
    {"id": 1, "subject": "Example issue", ...}
  ]
}
```

---

### 4. **Use Core Endpoints**
Common API endpoints (append `.json` or `.xml` for format):  
| Resource  | Endpoint                     | Method |
|-----------|------------------------------|--------|
| Issues    | `/issues.json`               | GET    |
| Projects  | `/projects.json`             | GET    |
| Time Entries | `/time_entries.json`       | POST   |
| Users     | `/users.json`                | GET    |

**Create an issue example:**
```bash
curl -X POST \
  -H "X-Redmine-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"issue": {"project_id": 1, "subject": "New issue", "priority_id": 2}}' \
  https://your-redmine-url.com/issues.json
```

---

### 5. **Explore the API Documentation**
- Official Redmine REST API guide:  
  [http://www.redmine.org/projects/redmine/wiki/Rest_api](http://www.redmine.org/projects/redmine/wiki/Rest_api)  
- Endpoint details, parameters, and examples are provided here.

---

### 6. **Use Client Libraries (Optional)**
Simplify integration with language-specific libraries:
- **Python:** [python-redmine](https://python-redmine.com)
- **Ruby:** [redmine-rest-api](https://github.com/edavis10/redmine)
- **PHP:** [Redmine PHP API Client](https://github.com/kbsali/php-redmine-api)

**Python example:**
```python
from redminelib import Redmine

redmine = Redmine(
    'https://your-redmine-url.com',
    key='YOUR_API_KEY'
)

# Get issue #123
issue = redmine.issue.get(123)
print(issue.subject)
```

---

### Key Notes:
- 🔐 **Permissions:** Your API key inherits your user permissions.
- 📦 **Data Formats:** Use `.json` (or `.xml`) in endpoints to specify response format.
- ⚠️ **Troubleshooting:**
  - `403 Forbidden`: Check API key/user permissions.
  - `404 Not Found`: Verify endpoint URL and Redmine base URL.
  - Enable logs in **Administration → Settings → API** for debugging.

Start with simple `GET` requests, then progress to `POST`/`PUT` operations.
