from fastapi import FastAPI, Query, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ---------------- DATA ---------------- #

courses = [
    {"id": 1, "title": "Python Basics", "instructor": "John", "category": "Web Dev", "level": "Beginner", "price": 999, "seats_left": 10},
    {"id": 2, "title": "Data Science", "instructor": "Alice", "category": "Data Science", "level": "Intermediate", "price": 1999, "seats_left": 5},
    {"id": 3, "title": "UI Design", "instructor": "Bob", "category": "Design", "level": "Beginner", "price": 0, "seats_left": 8},
    {"id": 4, "title": "DevOps", "instructor": "Sam", "category": "DevOps", "level": "Advanced", "price": 2999, "seats_left": 3},
    {"id": 5, "title": "React", "instructor": "John", "category": "Web Dev", "level": "Intermediate", "price": 1499, "seats_left": 7},
    {"id": 6, "title": "ML Basics", "instructor": "Alice", "category": "Data Science", "level": "Beginner", "price": 1200, "seats_left": 6},
]

enrollments = []
enrollment_counter = 1

wishlist = []

# ---------------- HELPERS ---------------- #

def find_course(course_id):
    for c in courses:
        if c["id"] == course_id:
            return c
    return None

def calculate_enrollment_fee(price, seats_left, coupon_code):
    discount = 0

    # early bird
    if seats_left > 5:
        discount += price * 0.1

    price_after = price - discount

    # coupons
    if coupon_code == "STUDENT20":
        discount += price_after * 0.2
    elif coupon_code == "FLAT500":
        discount += 500

    final = max(price - discount, 0)
    return round(final), round(discount)

def filter_courses_logic(category, level, max_price, has_seats):
    result = courses
    if category is not None:
        result = [c for c in result if c["category"] == category]
    if level is not None:
        result = [c for c in result if c["level"] == level]
    if max_price is not None:
        result = [c for c in result if c["price"] <= max_price]
    if has_seats is not None:
        if has_seats:
            result = [c for c in result if c["seats_left"] > 0]
        else:
            result = [c for c in result if c["seats_left"] == 0]
    return result

# ---------------- MODELS ---------------- #

class EnrollRequest(BaseModel):
    student_name: str = Field(..., min_length=2)
    course_id: int = Field(..., gt=0)
    email: str = Field(..., min_length=5)
    payment_method: str = "card"
    coupon_code: str = ""
    gift_enrollment: bool = False
    recipient_name: str = ""

class NewCourse(BaseModel):
    title: str = Field(..., min_length=2)
    instructor: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    level: str = Field(..., min_length=2)
    price: int = Field(..., ge=0)
    seats_left: int = Field(..., gt=0)

# ---------------- Q1–Q5 ---------------- #

@app.get("/")
def home():
    return {"message": "Welcome to LearnHub Online Courses"}

@app.get("/courses")
def get_courses():
    total_seats = sum(c["seats_left"] for c in courses)
    return {"courses": courses, "total": len(courses), "total_seats_available": total_seats}

@app.get("/courses/summary")
def summary():
    return {
        "total_courses": len(courses),
        "free_courses": len([c for c in courses if c["price"] == 0]),
        "most_expensive": max(courses, key=lambda x: x["price"]),
        "total_seats": sum(c["seats_left"] for c in courses),
        "category_count": {cat: len([c for c in courses if c["category"] == cat]) for cat in set(c["category"] for c in courses)}
    }
@app.get("/courses/filter")
def filter_courses(category: Optional[str]=None, level: Optional[str]=None, max_price: Optional[int]=None, has_seats: Optional[bool]=None):
    result = filter_courses_logic(category, level, max_price, has_seats)
    return {"results": result, "count": len(result)}
@app.get("/courses/search")
def search_courses(keyword: str):
    keyword = keyword.lower()

    result = [
        c for c in courses
        if keyword in c["title"].lower()
        or keyword in c["instructor"].lower()
        or keyword in c["category"].lower()
    ]

    return {
        "results": result,
        "total_found": len(result)
    }
@app.get("/courses/sort")
def sort_courses(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "title", "seats_left"]:
        raise HTTPException(400, "Invalid field")

    reverse = True if order == "desc" else False
    return sorted(courses, key=lambda x: x[sort_by], reverse=reverse)
@app.get("/courses/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    return {
        "data": courses[start:start+limit],
        "page": page,
        "total_pages": (len(courses) + limit - 1)//limit
    }
@app.get("/courses/browse")
def browse(keyword: Optional[str]=None, category: Optional[str]=None, level: Optional[str]=None,
           max_price: Optional[int]=None, sort_by: str="price", order: str="asc",
           page: int=1, limit: int=3):

    result = courses

    if keyword:
        result = [c for c in result if keyword.lower() in c["title"].lower()]
    if category:
        result = [c for c in result if c["category"] == category]
    if level:
        result = [c for c in result if c["level"] == level]
    if max_price:
        result = [c for c in result if c["price"] <= max_price]

    reverse = order == "desc"
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    start = (page-1)*limit
    return {
        "results": result[start:start+limit],
        "total": len(result),
        "page": page
    }
@app.get("/courses/{course_id}")
def get_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course

@app.get("/enrollments")
def get_enrollments():
    return {"enrollments": enrollments, "total": len(enrollments)}

# ---------------- Q6–Q10 ---------------- #
@app.get("/enrollments/search")
def search_enrollments(student_name: str):
    keyword = student_name.lower()

    result = [
        e for e in enrollments
        if keyword in e["student"].lower()
    ]

    return {
        "results": result,
        "total_found": len(result)
    }
@app.get("/enrollments/sort")
def sort_enrollments(order: str = "asc"):
    if order not in ["asc", "desc"]:
        raise HTTPException(400, "Invalid order")

    reverse = True if order == "desc" else False

    sorted_data = sorted(enrollments, key=lambda x: x["final_fee"], reverse=reverse)

    return {
        "results": sorted_data,
        "order": order
    }
@app.get("/enrollments/page")
def paginate_enrollments(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    total = len(enrollments)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": enrollments[start:end]
    }
@app.post("/enrollments")
def enroll(req: EnrollRequest):
    global enrollment_counter

    course = find_course(req.course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    if course["seats_left"] <= 0:
        raise HTTPException(400, "No seats available")

    if req.gift_enrollment and req.recipient_name == "":
        raise HTTPException(400, "Recipient name required")

    final_fee, discount = calculate_enrollment_fee(course["price"], course["seats_left"], req.coupon_code)

    course["seats_left"] -= 1

    enrollment = {
        "id": enrollment_counter,
        "student": req.student_name,
        "course": course["title"],
        "final_fee": final_fee,
        "discount": discount
    }

    if req.gift_enrollment:
        enrollment["gift_to"] = req.recipient_name

    enrollments.append(enrollment)
    enrollment_counter += 1

    return enrollment


# ---------------- Q11–Q15 ---------------- #

@app.post("/courses")
def add_course(course: NewCourse, response: Response):
    for c in courses:
        if c["title"].lower() == course.title.lower():
            raise HTTPException(400, "Duplicate course")

    new = course.dict()
    new["id"] = len(courses) + 1
    courses.append(new)

    response.status_code = 201
    return new


@app.put("/courses/{course_id}")
def update_course(course_id: int, price: Optional[int]=None, seats_left: Optional[int]=None):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Not found")

    if price is not None:
        course["price"] = price
    if seats_left is not None:
        course["seats_left"] = seats_left

    return course

@app.delete("/courses/{course_id}")
def delete_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Not found")

    for e in enrollments:
        if e["course"] == course["title"]:
            raise HTTPException(400, "Course has enrollments")

    courses.remove(course)
    return {"message": "Deleted"}

@app.post("/wishlist/add")
def add_wishlist(student_name: str, course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Not found")

    for w in wishlist:
        if w["student"] == student_name and w["course_id"] == course_id:
            raise HTTPException(400, "Duplicate")

    wishlist.append({"student": student_name, "course_id": course_id})
    return {"message": "Added"}

@app.get("/wishlist")
def get_wishlist():
    total_value = sum(find_course(w["course_id"])["price"] for w in wishlist)
    return {"wishlist": wishlist, "total_value": total_value}

@app.delete("/wishlist/remove/{course_id}")
def remove_wishlist(course_id: int, student_name: str):
    for w in wishlist:
        if w["course_id"] == course_id and w["student"] == student_name:
            wishlist.remove(w)
            return {"message": "Removed"}
    raise HTTPException(404, "Not found")

@app.post("/wishlist/enroll-all")
def enroll_all(student_name: str, payment_method: str):
    total = 0
    enrolled = []

    for w in wishlist[:]:
        if w["student"] == student_name:
            course = find_course(w["course_id"])
            if course and course["seats_left"] > 0:
                fee, _ = calculate_enrollment_fee(course["price"], course["seats_left"], "")
                total += fee
                course["seats_left"] -= 1
                enrolled.append(course["title"])
                wishlist.remove(w)

    return {"enrolled": enrolled, "total_fee": total}

# ---------------- Q16–Q20 ---------------- #






