const API_BASE = "http://127.0.0.1:8000";

const DEFAULT_AVATAR =
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232563eb'><path d='M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z'/></svg>";

function showAlert(message, type = "success") {
    const alertBox = document.getElementById("alertBox");
    alertBox.textContent = message;
    alertBox.className = `p-4 rounded-lg text-sm font-medium mb-4 ${
        type === "success"
            ? "bg-green-100 text-green-800 border border-green-300"
            : "bg-red-100 text-red-800 border border-red-300"
    }`;
    alertBox.classList.remove("hidden");
    setTimeout(() => alertBox.classList.add("hidden"), 6000);
}

function getToken() {
    return localStorage.getItem("educore_token");
}

function getRole() {
    return localStorage.getItem("educore_role");
}

function toggleForgotPassword() {
    const panel = document.getElementById("forgotPasswordPanel");
    panel.classList.toggle("hidden");
}

function readImageAsBase64(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            resolve("");
            return;
        }
        if (file.size > 1024 * 1024) {
            reject(new Error("Profile photo must be smaller than 1 MB."));
            return;
        }
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Failed to read image file."));
        reader.readAsDataURL(file);
    });
}

function updateUIState() {
    const token = getToken();
    const role = getRole();
    const authView = document.getElementById("authView");
    const adminDashboard = document.getElementById("adminDashboard");
    const studentDashboard = document.getElementById("studentDashboard");
    const logoutBtn = document.getElementById("logoutBtn");

    if (!token) {
        authView.classList.remove("hidden");
        adminDashboard.classList.add("hidden");
        studentDashboard.classList.add("hidden");
        logoutBtn.classList.add("hidden");
    } else if (role === "admin") {
        authView.classList.add("hidden");
        adminDashboard.classList.remove("hidden");
        studentDashboard.classList.add("hidden");
        logoutBtn.classList.remove("hidden");
        loadAdminData();
    } else if (role === "student") {
        authView.classList.add("hidden");
        adminDashboard.classList.add("hidden");
        studentDashboard.classList.remove("hidden");
        logoutBtn.classList.remove("hidden");
        loadStudentProfile();
    }
}

function logout() {
    localStorage.removeItem("educore_token");
    localStorage.removeItem("educore_role");
    showAlert("Logged out successfully.");
    updateUIState();
}

// Login Handler
document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const role = document.getElementById("loginRole").value;
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role, username, password }),
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Login failed");
        }
        localStorage.setItem("educore_token", data.token);
        localStorage.setItem("educore_role", data.role);
        showAlert(`Welcome back, ${username}!`);
        updateUIState();
    } catch (err) {
        showAlert(err.message, "error");
    }
});

// Forgot Password Handler
document.getElementById("forgotPasswordForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("resetEmail").value.trim();
    try {
        const res = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Password reset failed");
        showAlert(data.message);
        document.getElementById("forgotPasswordForm").reset();
        document.getElementById("forgotPasswordPanel").classList.add("hidden");
    } catch (err) {
        showAlert(err.message, "error");
    }
});

// Student Registration Handler (with Profile Photo)
document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("regFullName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const department = document.getElementById("regDepartment").value.trim();
    const gpa = parseFloat(document.getElementById("regGpa").value);
    const photoFile = document.getElementById("regPhotoFile").files[0];

    try {
        const photo_url = await readImageAsBase64(photoFile);
        const res = await fetch(`${API_BASE}/register-request`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ full_name, email, department, gpa, photo_url }),
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Registration failed");
        }
        showAlert(data.message);
        document.getElementById("registerForm").reset();
    } catch (err) {
        showAlert(err.message, "error");
    }
});

// Load Admin Dashboard Data
async function loadAdminData() {
    const token = getToken();
    try {
        const reqRes = await fetch(`${API_BASE}/student-requests`, {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (reqRes.status === 401) {
            logout();
            return;
        }

        const requests = await reqRes.json();
        renderRequestsTable(requests);
        await filterStudents();
    } catch (err) {
        showAlert("Failed to load admin data: " + err.message, "error");
    }
}

// Department Filtering & Search for Approved Students
async function filterStudents() {
    const token = getToken();
    const department = document.getElementById("departmentFilter").value;
    const search = document.getElementById("studentSearchInput").value.trim();

    const params = new URLSearchParams();
    if (department) params.append("department", department);
    if (search) params.append("search", search);

    try {
        const res = await fetch(`${API_BASE}/students?${params.toString()}`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
            logout();
            return;
        }
        const students = await res.json();
        renderStudentsTable(students);
    } catch (err) {
        showAlert("Failed to filter students: " + err.message, "error");
    }
}

function renderRequestsTable(requests) {
    const tbody = document.getElementById("requestsTableBody");
    tbody.innerHTML = "";
    if (requests.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-4 px-4 text-center text-gray-500">No registration requests found.</td></tr>`;
        return;
    }

    requests.forEach((req) => {
        const avatar = req.photo_url || DEFAULT_AVATAR;
        const statusBadge =
            req.status === "pending"
                ? `<span class="bg-yellow-100 text-yellow-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">Pending</span>`
                : req.status === "approved"
                ? `<span class="bg-green-100 text-green-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">Approved</span>`
                : `<span class="bg-red-100 text-red-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">Rejected</span>`;

        const actionButtons =
            req.status === "pending"
                ? `<div class="space-x-2">
                    <button onclick="approveRequest(${req.id})" class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs font-semibold">Approve</button>
                    <button onclick="rejectRequest(${req.id})" class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-semibold">Reject</button>
                   </div>`
                : `<span class="text-gray-400 text-xs">Processed</span>`;

        tbody.innerHTML += `
            <tr>
                <td class="py-3 px-4"><img src="${avatar}" alt="Avatar" class="w-9 h-9 rounded-full object-cover border bg-blue-50"></td>
                <td class="py-3 px-4 font-medium text-gray-900">${req.full_name}</td>
                <td class="py-3 px-4 text-gray-600">${req.email}</td>
                <td class="py-3 px-4 text-gray-600">${req.department}</td>
                <td class="py-3 px-4 text-gray-600">${req.gpa.toFixed(2)}</td>
                <td class="py-3 px-4">${statusBadge}</td>
                <td class="py-3 px-4">${actionButtons}</td>
            </tr>
        `;
    });
}

function renderStudentsTable(students) {
    const tbody = document.getElementById("studentsTableBody");
    tbody.innerHTML = "";
    if (students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="py-4 px-4 text-center text-gray-500">No approved students match the current filter.</td></tr>`;
        return;
    }

    students.forEach((stu) => {
        const avatar = stu.photo_url || DEFAULT_AVATAR;
        tbody.innerHTML += `
            <tr>
                <td class="py-3 px-4"><img src="${avatar}" alt="Avatar" class="w-9 h-9 rounded-full object-cover border bg-blue-50"></td>
                <td class="py-3 px-4 font-mono text-xs text-blue-700 font-semibold">${stu.student_code}</td>
                <td class="py-3 px-4 font-medium text-gray-900">${stu.full_name}</td>
                <td class="py-3 px-4 text-gray-700">${stu.username}</td>
                <td class="py-3 px-4 text-gray-600">${stu.email}</td>
                <td class="py-3 px-4"><span class="bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-md text-xs font-medium">${stu.department}</span></td>
                <td class="py-3 px-4 text-gray-600">${stu.gpa.toFixed(2)}</td>
                <td class="py-3 px-4">
                    <button onclick="deleteStudent(${stu.id})" class="text-red-600 hover:underline text-xs font-semibold">Delete</button>
                </td>
            </tr>
        `;
    });
}

async function approveRequest(id) {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/student-requests/${id}/approve`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Approval failed");
        showAlert(data.message);
        loadAdminData();
    } catch (err) {
        showAlert(err.message, "error");
    }
}

async function rejectRequest(id) {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/student-requests/${id}/reject`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Rejection failed");
        showAlert(data.message);
        loadAdminData();
    } catch (err) {
        showAlert(err.message, "error");
    }
}

async function deleteStudent(id) {
    if (!confirm("Are you sure you want to delete this student record?")) return;
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/students/${id}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Delete failed");
        showAlert(data.message);
        loadAdminData();
    } catch (err) {
        showAlert(err.message, "error");
    }
}

// Student Profile, Photo Update & Password Update
async function loadStudentProfile() {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/student/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
            logout();
            return;
        }
        const stu = await res.json();
        document.getElementById("studentAvatar").src = stu.photo_url || DEFAULT_AVATAR;
        document.getElementById("studentProfileDetails").innerHTML = `
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">Student ID</span><span class="font-bold text-blue-700">${stu.student_code}</span></div>
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">Full Name</span><span class="font-semibold text-gray-900">${stu.full_name}</span></div>
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">Username</span><span class="font-semibold text-gray-900">${stu.username}</span></div>
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">Email</span><span class="font-semibold text-gray-900">${stu.email}</span></div>
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">Department</span><span class="font-semibold text-gray-900">${stu.department}</span></div>
            <div class="p-3 bg-gray-50 rounded-lg"><span class="text-gray-500 block text-xs">GPA</span><span class="font-semibold text-gray-900">${stu.gpa.toFixed(2)}</span></div>
        `;
    } catch (err) {
        showAlert("Failed to load profile", "error");
    }
}

async function uploadNewStudentPhoto() {
    const token = getToken();
    const fileInput = document.getElementById("updatePhotoInput");
    const file = fileInput.files[0];
    if (!file) {
        showAlert("Please select an image file first.", "error");
        return;
    }

    try {
        const photo_url = await readImageAsBase64(file);
        const res = await fetch(`${API_BASE}/student/update-photo`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ photo_url }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to update photo");
        showAlert(data.message);
        fileInput.value = "";
        loadStudentProfile();
    } catch (err) {
        showAlert(err.message, "error");
    }
}

document.getElementById("changePasswordForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = getToken();
    const old_password = document.getElementById("oldPassword").value;
    const new_password = document.getElementById("newPassword").value;

    try {
        const res = await fetch(`${API_BASE}/student/change-password`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ old_password, new_password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Password update failed");
        showAlert(data.message);
        document.getElementById("changePasswordForm").reset();
    } catch (err) {
        showAlert(err.message, "error");
    }
});

// Initialize on page load
updateUIState();
