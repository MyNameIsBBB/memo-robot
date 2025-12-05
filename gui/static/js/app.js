let medicines = [];
let editingMedicineId = null;

function updateClock() {
    const now = new Date();
    const time = now.toLocaleTimeString("th-TH", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
    const date = now.toLocaleDateString("th-TH", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    });

    document.getElementById("time").textContent = time;
    document.getElementById("date").textContent = date;
}

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

async function loadMedicines() {
    try {
        const response = await fetch("/api/medicines");
        const data = await response.json();

        if (data.success) {
            medicines = data.medicines;
            renderMedicines(medicines);
            updateCount();
        }
    } catch (error) {
        showToast("เกิดข้อผิดพลาดในการโหลดข้อมูล", "error");
    }
}

function renderMedicines(medicineList) {
    const container = document.getElementById("medicineList");

    if (medicineList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>ไม่พบรายการยา</p>
                <p class="empty-hint">เพิ่มยาจากฟอร์มด้านขวา</p>
            </div>
        `;
        return;
    }

    container.innerHTML = medicineList
        .map(
            (medicine) => `
        <div class="medicine-card" data-id="${medicine.id}">
            <div class="card-header">
                <div>
                    <div class="card-title">${medicine.name}</div>
                    <div class="card-time">🕐 ${medicine.taken_time}</div>
                </div>
                <div class="card-actions">
                    <button class="btn-icon btn-edit" onclick="editMedicine(${
                        medicine.id
                    })">แก้ไข</button>
                    <button class="btn-icon btn-delete" onclick="deleteMedicine(${
                        medicine.id
                    })">ลบ</button>
                </div>
            </div>
            <div class="card-body">
                ${
                    medicine.dosage
                        ? `
                    <div class="card-info">
                        <span class="info-bullet">■</span>
                        <div><span class="info-label">ขนาดยา:</span>${medicine.dosage}</div>
                    </div>
                `
                        : ""
                }
                ${
                    medicine.uses && medicine.uses.length > 0
                        ? `
                    <div class="card-info">
                        <span class="info-bullet">■</span>
                        <div><span class="info-label">สรรพคุณ:</span>${medicine.uses.join(
                            ", "
                        )}</div>
                    </div>
                `
                        : ""
                }
                ${
                    medicine.side_effects && medicine.side_effects.length > 0
                        ? `
                    <div class="card-info">
                        <span class="info-bullet">■</span>
                        <div><span class="info-label">ผลข้างเคียง:</span>${medicine.side_effects.join(
                            ", "
                        )}</div>
                    </div>
                `
                        : ""
                }
            </div>
        </div>
    `
        )
        .join("");
}

function updateCount() {
    document.getElementById("medicineCount").textContent = medicines.length;
}

document
    .getElementById("medicineForm")
    .addEventListener("submit", async (e) => {
        e.preventDefault();

        const name = document.getElementById("medicineName").value.trim();
        const time = document.getElementById("medicineTime").value;
        const dosage = document.getElementById("medicineDosage").value.trim();
        const uses = document
            .getElementById("medicineUses")
            .value.split(",")
            .map((u) => u.trim())
            .filter((u) => u);
        const sideEffects = document
            .getElementById("medicineSideEffects")
            .value.split(",")
            .map((s) => s.trim())
            .filter((s) => s);

        if (!name || !time) {
            showToast("กรุณากรอกชื่อยาและเวลา", "error");
            return;
        }

        try {
            const response = await fetch("/api/medicines", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    taken_time: time,
                    dosage,
                    uses,
                    side_effects: sideEffects,
                }),
            });

            const data = await response.json();

            if (data.success) {
                showToast("เพิ่มยาสำเร็จ");
                document.getElementById("medicineForm").reset();
                document.getElementById("medicineTime").value = "08:00";
                loadMedicines();
            } else {
                showToast(data.message, "error");
            }
        } catch (error) {
            showToast("เกิดข้อผิดพลาด", "error");
        }
    });

function editMedicine(id) {
    const medicine = medicines.find((m) => m.id === id);
    if (!medicine) return;

    editingMedicineId = id;
    document.getElementById("editMedicineId").value = id;
    document.getElementById("editName").value = medicine.name;
    document.getElementById("editTime").value = medicine.taken_time;
    document.getElementById("editDosage").value = medicine.dosage || "";
    document.getElementById("editUses").value = medicine.uses
        ? medicine.uses.join(", ")
        : "";
    document.getElementById("editSideEffects").value = medicine.side_effects
        ? medicine.side_effects.join(", ")
        : "";

    document.getElementById("editModal").classList.add("active");
}

async function deleteMedicine(id) {
    if (!confirm("คุณต้องการลบยานี้ใช่หรือไม่?")) return;

    try {
        const response = await fetch(`/api/medicines/${id}`, {
            method: "DELETE",
        });

        const data = await response.json();

        if (data.success) {
            showToast("ลบยาสำเร็จ");
            loadMedicines();
        } else {
            showToast(data.message, "error");
        }
    } catch (error) {
        showToast("เกิดข้อผิดพลาด", "error");
    }
}

document.getElementById("editForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = editingMedicineId;
    const name = document.getElementById("editName").value.trim();
    const time = document.getElementById("editTime").value;
    const dosage = document.getElementById("editDosage").value.trim();
    const uses = document
        .getElementById("editUses")
        .value.split(",")
        .map((u) => u.trim())
        .filter((u) => u);
    const sideEffects = document
        .getElementById("editSideEffects")
        .value.split(",")
        .map((s) => s.trim())
        .filter((s) => s);

    try {
        const response = await fetch(`/api/medicines/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                taken_time: time,
                dosage,
                uses,
                side_effects: sideEffects,
            }),
        });

        const data = await response.json();

        if (data.success) {
            showToast("แก้ไขยาสำเร็จ");
            document.getElementById("editModal").classList.remove("active");
            loadMedicines();
        } else {
            showToast(data.message, "error");
        }
    } catch (error) {
        showToast("เกิดข้อผิดพลาด", "error");
    }
});

document.getElementById("closeModal").addEventListener("click", () => {
    document.getElementById("editModal").classList.remove("active");
});

document.getElementById("cancelEdit").addEventListener("click", () => {
    document.getElementById("editModal").classList.remove("active");
});

document.getElementById("setCurrentTime").addEventListener("click", () => {
    const now = new Date();
    const time = now.toTimeString().slice(0, 5);
    document.getElementById("medicineTime").value = time;
});

document.getElementById("refreshBtn").addEventListener("click", () => {
    loadMedicines();
    showToast("รีเฟรชข้อมูลแล้ว");
});

document.getElementById("resetBtn").addEventListener("click", () => {
    document.getElementById("medicineForm").reset();
    document.getElementById("medicineTime").value = "08:00";
});

document.getElementById("searchInput").addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = medicines.filter((m) =>
        m.name.toLowerCase().includes(query)
    );
    renderMedicines(filtered);
});

setInterval(updateClock, 1000);
updateClock();
loadMedicines();
