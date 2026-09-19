const userEmail = localStorage.getItem("userEmail");

async function loadProfile() {

    const response = await fetch("/profile");

    const user = await response.json();

    document.getElementById("fullName").innerText = user.full_name;
    document.getElementById("email").innerText = user.email;
    document.getElementById("phone").innerText = user.phone;
    document.getElementById("dob").innerText = user.dob;
    document.getElementById("dashboardTitle").innerText =
              user.role + " Dashboard";
    document.getElementById("role").innerText = user.role;
    localStorage.setItem("userId", user.id);
    const adminSection = document.getElementById("adminSection");
const teacherSection = document.getElementById("teacherSection");
const studentSection = document.getElementById("studentSection");
const updateProfileSection =
    document.getElementById("updateProfileSection");

adminSection.style.display = "none";
teacherSection.style.display = "none";
studentSection.style.display = "none";
updateProfileSection.style.display = "block";

if (user.role === "Admin") {

    adminSection.style.display = "block";

} else if (user.role === "Teacher") {

    teacherSection.style.display = "block";

}  else if (user.role === "Student") {

    studentSection.style.display = "block";
    updateProfileSection.style.display = "none";
}
    console.log("USER ROLE:", user.role);

    document.getElementById("editFullName").value = user.full_name;
    document.getElementById("editEmail").value = user.email;
    document.getElementById("editPhone").value = user.phone;
    document.getElementById("editDob").value = user.dob;
}

loadProfile();


document.getElementById("profileForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const fullName = document.getElementById("editFullName").value;
    const phone = document.getElementById("editPhone").value;
    const dob = document.getElementById("editDob").value;

    const response = await fetch("/update-profile", {
        method: "PUT",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
    full_name: fullName,
    phone: phone,
    dob: dob
})
    });

    const result = await response.json();

    document.getElementById("message").innerText = result.message;

    if (result.success) {
        loadProfile();
    }
});


document.getElementById("uploadButton").addEventListener("click", async function() {

    const fileInput = document.getElementById("profilePicture");
    const selectedFile = fileInput.files[0];

    if (!selectedFile) {
        document.getElementById("message").innerText =
            "Please select a picture first!";
        return;
    }

    const formData = new FormData();
formData.append("file", selectedFile);

    try {
        const response = await fetch("/upload-profile-picture", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        console.log("BACKEND RESPONSE:", result);

        document.getElementById("message").innerText =
            result.message || "No message received";

        if (result.success === true && result.image_url) {
            document.getElementById("profileImage").src =
                result.image_url + "?t=" + new Date().getTime();
        } else {
            document.getElementById("message").innerText =
                JSON.stringify(result);
        }

    } catch (error) {
        console.log("UPLOAD ERROR:", error);

        document.getElementById("message").innerText =
            "Upload error: " + error.message;
    }
});

document.getElementById("deletePictureButton").addEventListener("click", async function() {

   const response = await fetch(
    "/delete-profile-picture",
    {
        method: "DELETE"
    }
);

    const result = await response.json();

    document.getElementById("message").innerText = result.message;

    if (result.success === true) {
        document.getElementById("profileImage").src = "";
    }
});

function logoutUser() {
    localStorage.removeItem("userEmail");
    window.location.href = "/logout";
}
async function showAdminMessage() {

    console.log("MANAGE USERS BUTTON CLICKED");

    const response = await fetch("/admin/users");

    const result = await response.json();

    console.log("ADMIN USERS:", result);

    const userList = document.getElementById("userList");

    userList.innerHTML = "";

    if (result.users.length === 0) {
        userList.innerText = "No Teachers or Students found.";
        return;
    }

    result.users.forEach(function(user) {

        const userDiv = document.createElement("div");

    userDiv.innerHTML = `
    <hr>

    <p><strong>Name:</strong> ${user.full_name}</p>

    <p><strong>Email:</strong> ${user.email}</p>

    <p><strong>Phone:</strong> ${user.phone}</p>

    <p><strong>Role:</strong> ${user.role}</p>

    <p><strong>Subject:</strong> ${user.subject || "N/A"}</p>

    <p><strong>Standard:</strong> ${user.standard || "N/A"}</p>

    <button type="button" onclick="editUser(${user.id})">
    Update User
</button>

<button type="button" onclick="deleteUser(${user.id})">
    Delete User
</button>
`;

        userList.appendChild(userDiv);
    });

    document.getElementById("adminMessage").innerText =
        "Users loaded successfully!";
}

document.getElementById("newRole").addEventListener("change", function() {

    const role = this.value;

    const teacherFields = document.getElementById("newTeacherFields");
    const studentFields = document.getElementById("newStudentFields");

    if (role === "Teacher") {

        teacherFields.style.display = "block";
        studentFields.style.display = "none";

    } else if (role === "Student") {

        teacherFields.style.display = "none";
        studentFields.style.display = "block";

    } else {

        teacherFields.style.display = "none";
        studentFields.style.display = "none";

    }

});

document.getElementById("createUserForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const fullName = document.getElementById("newFullName").value;
    const email = document.getElementById("newEmail").value;
    const phone = document.getElementById("newPhone").value;
    const dob = document.getElementById("newDob").value;
    const role = document.getElementById("newRole").value;
    const subject = document.getElementById("newSubject").value;
    const standard = document.getElementById("newStandard").value;

    const response = await fetch("/admin/create-user", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            full_name: fullName,
            email: email,
            phone: phone,
            dob: dob,
            role: role,
            subject: subject,
            standard: standard
        })
    });

    const result = await response.json();

    document.getElementById("createUserMessage").innerText =
    result.message + "\nTemporary Password: " + result.temporary_password;

    if (result.success) {
        document.getElementById("createUserForm").reset();

        document.getElementById("newTeacherFields").style.display = "none";
        document.getElementById("newStudentFields").style.display = "none";
    }

});
async function editUser(userId) {

    const fullName = prompt("Enter new full name:");

    if (fullName === null) {
        return;
    }

    const phone = prompt("Enter new phone number:");

    if (phone === null) {
        return;
    }

    const dob = prompt("Enter new date of birth (YYYY-MM-DD):");

    if (dob === null) {
        return;
    }

    const role = prompt("Enter role (Teacher or Student):");

    if (role === null) {
        return;
    }

    let subject = "";
    let standard = "";

    if (role === "Teacher") {

        subject = prompt("Enter subject:");

        if (subject === null) {
            return;
        }

    } else if (role === "Student") {

        standard = prompt("Enter standard:");

        if (standard === null) {
            return;
        }

    } else {

        alert("Invalid role! Please enter Teacher or Student.");
        return;
    }


    const response = await fetch(`/admin/update-user/${userId}`, {

        method: "PUT",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            full_name: fullName,
            phone: phone,
            dob: dob,
            role: role,
            subject: subject,
            standard: standard

        })

    });


    const result = await response.json();


    alert(result.message);


    if (result.success) {

        showAdminMessage();

    }
        
}
async function deleteUser(userId) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this user?"
    );

    if (!confirmDelete) {
        return;
    }

    const response = await fetch(
        `/admin/delete-user/${userId}`,
        {
            method: "DELETE"
        }
    );

    const result = await response.json();

    alert(result.message);

    if (result.success) {
        showAdminMessage();
    }

}
async function loadAssignmentUsers() {

    const response = await fetch("/admin/users");

    const result = await response.json();

    const studentSelect = document.getElementById("studentSelect");
    const teacherSelect = document.getElementById("teacherSelect");

    // Clear old options
    studentSelect.innerHTML = `
        <option value="">Select Student</option>
    `;

    teacherSelect.innerHTML = `
        <option value="">Select Teacher</option>
    `;


    result.users.forEach(function(user) {

        if (user.role === "Student") {

            const option = document.createElement("option");

            option.value = user.id;
            option.textContent = user.full_name;

            studentSelect.appendChild(option);
        }


        if (user.role === "Teacher") {

            const option = document.createElement("option");

            option.value = user.id;
            option.textContent = user.full_name;

            teacherSelect.appendChild(option);
        }

    });

}


// Load Students and Teachers
loadAssignmentUsers();
async function assignTeacher() {

    const studentId = document.getElementById("studentSelect").value;
    const teacherId = document.getElementById("teacherSelect").value;

    const message = document.getElementById("assignmentMessage");

    if (!studentId) {
        message.innerText = "Please select a Student!";
        return;
    }

    if (!teacherId) {
        message.innerText = "Please select a Teacher!";
        return;
    }

    const response = await fetch(`/admin/assign-teacher/${studentId}`, {

        method: "PUT",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            teacher_id: parseInt(teacherId)
        })

    });

    const result = await response.json();

    message.innerText = result.message;

}
async function loadTeacherStudents() {

    const response = await fetch("/teacher/students");

    const result = await response.json();

    const studentList = document.getElementById("teacherStudentList");
    const message = document.getElementById("teacherMessage");

    studentList.innerHTML = "";

    if (!result.students || result.students.length === 0) {

        message.innerText = "No students assigned to you.";

        return;
    }

    message.innerText =
        "Assigned students loaded successfully!";

    result.students.forEach(function(student) {

        const studentDiv = document.createElement("div");

        studentDiv.innerHTML = `
    <hr>

    <p><strong>Name:</strong> ${student.full_name}</p>

    <p><strong>Email:</strong> ${student.email}</p>

    <p><strong>Phone:</strong> ${student.phone}</p>

    <p><strong>Date of Birth:</strong> ${student.dob}</p>

    <p><strong>Standard:</strong> ${student.standard || "N/A"}</p>

    <button type="button" onclick="updateAssignedStudent(${student.id})">
        Update Student
    </button>
`;
        studentList.appendChild(studentDiv);

    });
}
async function loadStudentTeacher() {

    const response = await fetch("/student/teacher");

    const result = await response.json();

    const message = document.getElementById("studentMessage");
    const teacherInfo = document.getElementById("studentTeacherInfo");

    teacherInfo.innerHTML = "";

    if (!result.success) {

        message.innerText = result.message;

        return;
    }

    message.innerText = "Teacher information loaded successfully!";

    teacherInfo.innerHTML = `
        <hr>

        <p>
            <strong>Teacher Name:</strong>
            ${result.teacher.full_name}
        </p>

        <p>
            <strong>Email:</strong>
            ${result.teacher.email}
        </p>

        <p>
            <strong>Subject:</strong>
            ${result.teacher.subject || "N/A"}
        </p>
    `;
}
async function updateAssignedStudent(studentId) {

    const fullName = prompt("Enter student's new full name:");

    if (fullName === null) {
        return;
    }

    const phone = prompt("Enter student's new phone number:");

    if (phone === null) {
        return;
    }

    const dob = prompt("Enter student's new date of birth (YYYY-MM-DD):");

    if (dob === null) {
        return;
    }

    const standard = prompt("Enter student's new standard:");

    if (standard === null) {
        return;
    }

    const response = await fetch(
        `/teacher/update-student/${studentId}`,
        {
            method: "PUT",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                full_name: fullName,
                phone: phone,
                dob: dob,
                standard: standard
            })
        }
    );

    const result = await response.json();

    alert(result.message);

    if (result.success) {
        loadTeacherStudents();
    }
}