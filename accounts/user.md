.\venv\Scripts\Activate.ps1

stripe listen --forward-to localhost:8000/api/payments/webhook/

celery beat 

python -m celery -A b2b_course_platform beat -l info

celery worker for windows we have to manaully create it on multiple terminal

python -m celery -A b2b_course_platform worker -l info -P solo -Q default_queue --hostname=default_worker@%h

python -m celery -A b2b_course_platform worker -l info -P solo -Q email_queue (chnge this name to create the multiple worker)--hostname=email_worker_@%h

celery flower

python -m celery -A b2b_course_platform flower

superadmin

{
  "email": "superadmin@platform.com",
  "password": "SuperAdmin123!"
}

create tenant

{
    "name": "infosys",
    "slug": "infosys",
    "description": "Infosys is a global leader in next-generation digital services and consulting.",
    "is_active": true
}


infosys admin

{
    "email": "admin@infosys.com",
    "username": "infosys_admin",
    "password": "password123",
    "first_name": "Ravi",
    "last_name": "Kumar",
    "tenant": "infosys"
}

create tenant

{
    "name": "ibm",
    "slug": "ibm",
    "description": "IBM is a global leader in next-generation digital services and consulting.",
    "is_active": true
}


IBM admin
{
    "email": "admin@ibm.com",
    "username": "ibm_admin",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "tenant": "ibm"
}

create tenant

{
    "name": "amazon",
    "slug": "amazon",
    "description": "Amazon is a global leader in next-generation digital services and consulting.",
    "is_active": true
}

Amazon admin
{
    "email": "admin@amazon.com",
    "username": "amazon_admin",
    "password": "password123",
    "first_name": "Jane",
    "last_name": "Smith",
    "tenant": "amazon"
}



users of tenant infosys make it user 1 and user2 

{
    "email": "user@infosys.com",
    "username": "infosys_user",
    "password": "password123",
    "first_name": "Harish",
    "last_name": "Kumar",
    "tenant": "infosys"
}

users of tenant ibm make it user 1 and user2 

{
    "email": "user@ibm.com",
    "username": "ibm_user",
    "password": "password123",
    "first_name": "David",
    "last_name": "Mavanee",
    "tenant": "ibm"
}

users of tenant amazon make it user 1 and user2 

{
    "email": "user@amazon.com",
    "username": "amazon_user",
    "password": "password123",
    "first_name": "MS",
    "last_name": "Dhoni",
    "tenant": "amazon"
}


{
    "email": "content@example.com",
    "username": "content_mgr",
    "password": "securePass123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "CONTENT_MANAGER",
    "tenant": "acme-corp"
}