const API_BASE = '/api';
let currentStockTab = 'purchase';
let currentVendor = null;

function showSection(sectionId) {
    // Show popup for reminders section
    if (sectionId === 'reminders') {
        // Check if popup has been shown in this session
        if (!sessionStorage.getItem('remindersPopupShown')) {
            showReminderPopup();
            return; // Don't switch sections yet
        }
    }
    
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    document.querySelector(`.nav-tab[onclick="showSection('${sectionId}')"]`).classList.add('active');
    loadSectionData(sectionId);
}

function loadSectionData(sectionId) {
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to view data.', 'error');
        showAuthModal();
        return;
    }
    switch(sectionId) {
        case 'reminders': loadReminders(); break;
        case 'stock': loadStockData('all'); break;
        case 'events': loadEvents(); break;
    }
}

function showReminderPopup() {
    document.getElementById('reminderPopup').style.display = 'flex';
}

function closeReminderPopup() {
    document.getElementById('reminderPopup').style.display = 'none';
    // Mark that popup has been shown
    sessionStorage.setItem('remindersPopupShown', 'true');
    // Now switch to reminders section
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById('reminders').classList.add('active');
    document.querySelector(`.nav-tab[onclick="showSection('reminders')"]`).classList.add('active');
    loadSectionData('reminders');
}

async function loadReminders() {
    if (!currentVendor || !currentVendor.id) {
        showAlert('reminderAlert', 'Please log in to view reminders.', 'error');
        showAuthModal();
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/reminders/?vendor_id=${encodeURIComponent(currentVendor.id)}`, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.status === 401) {
            showAuthModal();
            return;
        }
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Server error: ${response.status} - ${text}`);
        }
        const reminders = await response.json();
        displayReminders(reminders);
    } catch (error) {
        console.error('Error in loadReminders:', error);
        showAlert('reminderAlert', `Error loading reminders: ${error.message}`, 'error');
    }
}

function displayReminders(reminders) {
    const container = document.getElementById('remindersList');
    if (reminders.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">No reminders found</p>';
        return;
    }
    container.innerHTML = reminders.map(reminder => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">${reminder.item_name}</div>
                <div class="card-actions">
                    <button class="btn btn-sm btn-danger" onclick="deleteReminder(${reminder.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <p><strong>Amount:</strong> &#8377;${reminder.Amount}</p>
            <p><strong>To:</strong> ${reminder.ToWhom}</p>
            <p><strong>Phone:</strong> ${reminder.phone_number}</p>
            <p><strong>Reminder:</strong> ${new Date(reminder.Date_Time).toLocaleString()}</p>
            <p><strong>Payment:</strong> ${reminder.payment_method}</p>
        </div>
    `).join('');
}

async function loadStockData(type = 'all') {
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to view stock data.', 'error');
        showAuthModal();
        return;
    }
    try {
        showLoading('stockLoading', true);
        let purchases = [], sales = [];
        if (type === 'all' || type === 'purchase') {
            const purchaseResponse = await fetch(`${API_BASE}/purchases/`, { credentials: 'include' });
            if (purchaseResponse.status === 401) {
                showAuthModal();
                return;
            }
            purchases = await purchaseResponse.json();
        }
        if (type === 'all' || type === 'sale') {
            const saleResponse = await fetch(`${API_BASE}/sales/`, { credentials: 'include' });
            if (saleResponse.status === 401) {
                showAuthModal();
                return;
            }
            sales = await saleResponse.json();
        }
        displayStockData(purchases, sales, type);
    } catch (error) {
        showAlert('stockAlert', 'Error loading stock data: ' + error.message, 'error');
    } finally {
        showLoading('stockLoading', false);
    }
}

function displayStockData(purchases, sales, type = 'all') {
    const container = document.getElementById('stockList');
    let allTransactions = [];
    if (type === 'all') {
        allTransactions = [
            ...purchases.map(p => ({...p, type: 'purchase'})),
            ...sales.map(s => ({...s, type: 'sale'}))
        ].sort((a, b) => new Date(b.created_at || b.date) - new Date(a.created_at || a.date));
    } else if (type === 'purchase') {
        allTransactions = purchases.map(p => ({...p, type: 'purchase'})).sort((a, b) => new Date(b.created_at || b.date) - new Date(a.created_at || a.date));
    } else if (type === 'sale') {
        allTransactions = sales.map(s => ({...s, type: 'sale'})).sort((a, b) => new Date(b.created_at || b.date) - new Date(a.created_at || a.date));
    }
    if (allTransactions.length === 0) {
        const message = type === 'all' ? 'No transactions found' : type === 'purchase' ? 'No purchase transactions found' : 'No sale transactions found';
        container.innerHTML = `<p style="text-align: center; color: #666;">${message}</p>`;
        return;
    }
    container.innerHTML = `
        <div class="table-container">
            <table class="table stock-table">
                <thead>
                    <tr><th>Type</th><th>Item</th><th>Quantity</th><th>Price</th><th>Payment</th><th>Date</th><th style="text-align:center;">Actions</th></tr>
                </thead>
                <tbody>
                    ${allTransactions.map(t => `
                        <tr>
                            <td data-label="Type"><span style="color: ${t.type === 'purchase' ? '#28a745' : '#dc3545'}; font-weight: bold; display: flex; align-items: center; gap: 0.3rem;"><i class="fas ${t.type === 'purchase' ? 'fa-arrow-down' : 'fa-arrow-up'}"></i> ${t.type === 'purchase' ? 'Purchase' : 'Sale'}</span></td>
                            <td data-label="Item">${t.item_name}</td>
                            <td data-label="Quantity">${t.quantity}</td>
                            <td data-label="Price"><span style="font-family:inherit;">&#8377;${t.price || t.total_price}</span></td>
                            <td data-label="Payment">${t.payment_method}</td>
                            <td data-label="Date">${new Date(t.created_at || t.date).toLocaleDateString()}</td>
                            <td data-label="Actions" style="text-align:center;">
                                <span style="display:inline-flex; gap:1.25rem; align-items:center;">
                                    <button class="btn btn-sm btn-success" title="Edit" style="display:flex;align-items:center;gap:0.3rem;" onclick="openEditModal('${t.type}', ${t.id}, this)"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19.5 3 21l1.5-4L16.5 3.5z"/></svg></button>
                                    <button class="btn btn-sm btn-danger" title="Delete" style="display:flex;align-items:center;gap:0.3rem;" onclick="deleteTransaction('${t.type}', ${t.id})"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></button>
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function loadEvents() {
    if (!currentVendor || !currentVendor.id) {
        showAlert('eventsAlert', 'Please log in to view events.', 'error');
        showLoading('eventsLoading', false);
        return;
    }
    showLoading('eventsLoading', true);
    try {
        const vendorId = currentVendor.id;
        const response = await fetch(`${API_BASE}/vendor-events/events?vendor_id=${encodeURIComponent(vendorId)}`, { credentials: 'include' });
        if (response.status === 401) {
            showAuthModal();
            return;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const events = await response.json();
        displayEvents(events);
    } catch (error) {
        showAlert('eventsAlert', 'Error loading events: ' + error.message, 'error');
    } finally {
        showLoading('eventsLoading', false);
    }
}

function displayEvents(events) {
    const container = document.getElementById('eventsList');
    if (events.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">No upcoming events found for your location.</p>';
        return;
    }
    container.innerHTML = events.map(event => `
        <div class="feature-card">
            <div class="feature-title">${event.event_name}</div>
            <div class="feature-desc">${event.description}</div>
            <div class="event-info">
                <p><strong>Location:</strong> ${event.location}</p>
                <p><strong>Date:</strong> ${event.event_date || 'TBA'}</p>
                <p><strong>Contact:</strong> ${event.contact_phone || 'N/A'}</p>
                <p><strong>Stall Info:</strong> ${event.stall_info}</p>
                <a href="${event.source_url}" target="_blank">More Info</a>
            </div>
        </div>
    `).join('');
}

async function loadVendorDetails() {
    if (!currentVendor || !currentVendor.PhoneNumber) return; // Skip if no vendor or phone number
    try {
        const response = await fetch(`${API_BASE}/vendor/by-phone/${encodeURIComponent(currentVendor.PhoneNumber)}`, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to fetch vendor details: ${response.status}`);
        currentVendor = await response.json();
        document.getElementById('phoneNumber').value = currentVendor.PhoneNumber || '';
        document.getElementById('profileName').value = currentVendor.Name || '';
        document.getElementById('profilePhone').value = currentVendor.PhoneNumber || '';
        document.getElementById('profileAddress').value = currentVendor.Location || '';
    } catch (err) {
        console.error(err);
        showAlert('reminderAlert', 'Error loading vendor details', 'error');
    }
}

document.getElementById('reminderForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentVendor || !currentVendor.PhoneNumber) {
        showAlert('reminderAlert', 'Please log in', 'error');
        return;
    }

    showLoading('reminderLoading', true);

    const dateTime = document.getElementById('reminderDateTime').value;
    if (!dateTime) {
        showAlert('reminderAlert', 'Please pick a date/time', 'error');
        showLoading('reminderLoading', false);
        return;
    }
    const selectedDate = new Date(dateTime);
    if (isNaN(selectedDate) || selectedDate < new Date()) {
        showAlert('reminderAlert', 'Invalid future date', 'error');
        showLoading('reminderLoading', false);
        return;
    }

    const itemName = document.getElementById('itemName').value.trim();
    const amount = parseFloat(document.getElementById('amount').value);
    const toWhom = document.getElementById('toWhom').value.trim();
    const supplier = document.getElementById('supplierPhone').value.trim();
    const payment = document.getElementById('paymentMethod').value;

    if (!itemName || isNaN(amount) || amount <= 0 || !toWhom || !supplier) {
        showAlert('reminderAlert', 'Fill all fields', 'error');
        showLoading('reminderLoading', false);
        return;
    }

    const payload = {
        Date_Time: dateTime,
        item_name: itemName,
        Amount: amount,
        ToWhom: toWhom,
        phone_number: document.getElementById('phoneNumber').value.trim(),
        supplier_phone_number: supplier,
        payment_method: payment
    };

    try {
        const response = await fetch(`${API_BASE}/schedule-payment-reminder`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const txt = await response.text();
            throw new Error(`${response.status} – ${txt}`);
        }
        showAlert('reminderAlert', 'Reminder created!', 'success');
        document.getElementById('reminderForm').reset();
        document.getElementById('phoneNumber').value = currentVendor.PhoneNumber;
        loadReminders();
    } catch (err) {
        console.error(err);
        showAlert('reminderAlert', `Error: ${err.message}`, 'error');
    } finally {
        showLoading('reminderLoading', false);
    }
});

document.getElementById('saleFormElement').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to add sales.', 'error');
        showAuthModal();
        return;
    }
    showLoading('stockLoading', true);
    try {
        const formData = {
            item_name: document.getElementById('saleItemName').value,
            quantity: parseInt(document.getElementById('saleQuantity').value),
            total_price: parseFloat(document.getElementById('saleTotalPrice').value),
            payment_method: document.getElementById('salePaymentMethod').value
        };
        const response = await fetch(`${API_BASE}/sales/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData),
            credentials: 'include'
        });
        if (response.status === 401) {
            showAuthModal();
            return;
        }
        if (response.ok) {
            showAlert('stockAlert', 'Sale added successfully!', 'success');
            document.getElementById('saleFormElement').reset();
            loadStockData(currentStockTab);
        } else {
            throw new Error('Failed to add sale');
        }
    } catch (error) {
        showAlert('stockAlert', 'Error adding sale: ' + error.message, 'error');
    } finally {
        showLoading('stockLoading', false);
    }
});

document.getElementById('receiptFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImage').src = e.target.result;
            document.getElementById('filePreview').style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

function showScanLoading(show) {
    document.getElementById('scanLoading').style.display = show ? 'block' : 'none';
}

document.getElementById('scanForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentVendor) {
        showAlert('scanAlert', 'Please log in to process receipts.', 'error');
        showAuthModal();
        return;
    }
    document.getElementById('scanAlert').innerHTML = '';
    document.getElementById('scanResults').style.display = 'none';
    try {
        const file = document.getElementById('receiptFile').files[0];
        const intentElement = document.querySelector('input[name="intent"]:checked');
        if (!file) {
            throw new Error('Please select a receipt image to upload');
        }
        if (!intentElement) {
            throw new Error('Please select transaction type (Purchase or Sale)');
        }
        const intent = intentElement.value;
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type.toLowerCase())) {
            throw new Error('Please upload a valid image file (JPG, PNG, GIF, or WebP)');
        }
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            throw new Error('File size too large. Please upload an image smaller than 10MB');
        }
        showScanLoading(true);
        document.getElementById('scanLoadingText').textContent = 'Processing receipt with AI...';
        const formData = new FormData();
        formData.append('file', file);
        formData.append('intent', intent);
        const response = await fetch('/api/upload-receipt/', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        if (response.status === 401) {
            showAuthModal();
            return;
        }
        if (!response.ok) {
            let errorMessage = 'Failed to process receipt';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        const result = await response.json();
        if (!result || !result.items || !Array.isArray(result.items)) {
            throw new Error('Invalid response format from server');
        }
        if (result.items.length === 0) {
            showAlert('scanAlert', 'No items were found in the receipt image. Please try with a clearer image.', 'error');
            return;
        }
        showAlert('scanAlert', `Receipt processed successfully! Found ${result.items.length} item(s). You can edit them below before saving.`, 'success');
        displayScanResults(result.items);
        document.getElementById('scanForm').reset();
        document.getElementById('filePreview').style.display = 'none';
    } catch (error) {
        let errorMessage = error.message;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again with a smaller image or check your internet connection.';
        } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
            errorMessage = 'Network error. Please check your internet connection and try again.';
        }
        console.error('Receipt processing error:', error);
        showAlert('scanAlert', 'Error processing receipt: ' + errorMessage, 'error');
    } finally {
        showScanLoading(false);
    }
});

function displayScanResults(items) {
    const container = document.getElementById('extractedItems');
    if (!Array.isArray(items) || items.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#666;">No items found in the receipt.</p>';
        document.getElementById('scanResults').style.display = 'block';
        return;
    }
    try {
        container.innerHTML = `
            <div class="table-container">
                <table class="table stock-table">
                    <thead>
                        <tr>
                            <th>Item Name</th>
                            <th>Quantity</th>
                            <th>Price (₹)</th>
                            <th>Payment Method</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map((item, idx) => {
                            const itemName = (item.item_name || '').toString();
                            const quantity = Math.max(1, parseInt(item.quantity) || 1);
                            const price = Math.max(0, parseFloat(item.price) || 0);
                            const paymentMethod = (item.payment_method === 'online') ? 'online' : 'Cash';
                            return `
                                <tr id="scan-item-${idx}">
                                    <td data-label="Item Name">
                                        <input type="text" name="item_name_${idx}" value="${itemName}" class="form-input" required placeholder="Enter item name">
                                    </td>
                                    <td data-label="Quantity">
                                        <input type="number" name="quantity_${idx}" value="${quantity}" class="form-input" min="1" required>
                                    </td>
                                    <td data-label="Price">
                                        <input type="number" name="price_${idx}" value="${price}" class="form-input" min="0" step="0.01" required>
                                    </td>
                                    <td data-label="Payment Method">
                                        <select name="payment_method_${idx}" class="form-select" required>
                                            <option value="Cash" ${paymentMethod === 'Cash' ? 'selected' : ''}>Cash</option>
                                            <option value="online" ${paymentMethod === 'online' ? 'selected' : ''}>Online</option>
                                        </select>
                                    </td>
                                    <td data-label="Actions" style="text-align:center;">
                                        <button type="button" class="btn btn-sm btn-danger" onclick="removeScannedItem(${idx})" title="Remove this item">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            <input type="hidden" name="item_count" value="${items.length}">
            <div style="margin-top: 1rem; text-align: center;">
                <button type="button" class="btn btn-secondary" onclick="addScannedItem()">
                    <i class="fas fa-plus"></i> Add Item
                </button>
            </div>
        `;
        document.getElementById('scanResults').style.display = 'block';
    } catch (error) {
        console.error('Error displaying scan results:', error);
        container.innerHTML = '<p style="text-align:center; color:#ff0000;">Error displaying results. Please try again.</p>';
        document.getElementById('scanResults').style.display = 'block';
    }
}

function removeScannedItem(index) {
    const row = document.getElementById(`scan-item-${index}`);
    if (row) {
        row.remove();
        updateItemCount();
    }
}

function addScannedItem() {
    const tbody = document.querySelector('#extractedItems tbody');
    const currentCount = tbody.children.length;
    const newRow = document.createElement('tr');
    newRow.id = `scan-item-${currentCount}`;
    newRow.innerHTML = `
        <td data-label="Item Name">
            <input type="text" name="item_name_${currentCount}" class="form-input" required placeholder="Enter item name">
        </td>
        <td data-label="Quantity">
            <input type="number" name="quantity_${currentCount}" value="1" class="form-input" min="1" required>
        </td>
        <td data-label="Price">
            <input type="number" name="price_${currentCount}" value="0" class="form-input" min="0" step="0.01" required>
        </td>
        <td data-label="Payment Method">
            <select name="payment_method_${currentCount}" class="form-select" required>
                <option value="Cash" selected>Cash</option>
                <option value="online">Online</option>
            </select>
        </td>
        <td data-label="Actions" style="text-align:center;">
            <button type="button" class="btn btn-sm btn-danger" onclick="removeScannedItem(${currentCount})" title="Remove this item">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(newRow);
    updateItemCount();
}

function updateItemCount() {
    const itemCountInput = document.querySelector('input[name="item_count"]');
    const rows = document.querySelectorAll('#extractedItems tbody tr');
    if (itemCountInput) {
        itemCountInput.value = rows.length;
    }
}

function showLoading(elementId, show) {
    document.getElementById(elementId).style.display = show ? 'block' : 'none';
}

function showAlert(elementId, message, type) {
    const alertDiv = document.getElementById(elementId);
    alertDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => alertDiv.innerHTML = '', 5000);
}

async function deleteReminder(id) {
    if (!currentVendor) {
        showAlert('reminderAlert', 'Please log in to delete reminders.', 'error');
        showAuthModal();
        return;
    }
    if (confirm('Are you sure you want to delete this reminder?')) {
        try {
            const response = await fetch(`${API_BASE}/reminders/${id}`, { method: 'DELETE', credentials: 'include' });
            if (response.status === 401) {
                showAuthModal();
                return;
            }
            if (response.ok) {
                showAlert('reminderAlert', 'Reminder deleted successfully!', 'success');
                loadReminders();
            } else {
                throw new Error('Failed to delete reminder');
            }
        } catch (error) {
            showAlert('reminderAlert', 'Error deleting reminder: ' + error.message, 'error');
        }
    }
}

async function deleteTransaction(type, id) {
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to delete transactions.', 'error');
        showAuthModal();
        return;
    }
    if (confirm('Are you sure you want to delete this transaction?')) {
        try {
            const endpoint = type === 'purchase' ? 'purchases' : 'sales';
            const response = await fetch(`${API_BASE}/${endpoint}/${id}`, { method: 'DELETE', credentials: 'include' });
            if (response.status === 401) {
                showAuthModal();
                return;
            }
            if (response.ok) {
                showAlert('stockAlert', 'Transaction deleted successfully!', 'success');
                loadStockData(currentStockTab);
            } else {
                throw new Error('Failed to delete transaction');
            }
        } catch (error) {
            showAlert('stockAlert', 'Error deleting transaction: ' + error.message, 'error');
        }
    }
}

function openEditModal(type, id, btn) {
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to edit transactions.', 'error');
        showAuthModal();
        return;
    }
    let row = btn.closest('tr');
    let itemName = row.children[1].textContent;
    let quantity = row.children[2].textContent;
    let price = row.children[3].textContent.replace('₹', '').replace('&#8377;', '');
    let payment = row.children[4].textContent;
    document.getElementById('editStockType').value = type;
    document.getElementById('editStockId').value = id;
    document.getElementById('editItemName').value = itemName;
    document.getElementById('editQuantity').value = quantity;
    document.getElementById('editPrice').value = price;
    document.getElementById('editPaymentMethod').value = payment;
    document.getElementById('editModalTitle').textContent = type === 'purchase' ? 'Edit Purchase' : 'Edit Sale';
    document.getElementById('editPriceLabel').textContent = type === 'purchase' ? 'Price (₹)' : 'Total Price (₹)';
    document.getElementById('editModal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

document.getElementById('editStockForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to edit transactions.', 'error');
        showAuthModal();
        return;
    }
    showLoading('stockLoading', true);
    try {
        const type = document.getElementById('editStockType').value;
        const id = document.getElementById('editStockId').value;
        const data = {
            item_name: document.getElementById('editItemName').value,
            quantity: parseInt(document.getElementById('editQuantity').value),
            payment_method: document.getElementById('editPaymentMethod').value
        };
        if (type === 'purchase') data.price = parseFloat(document.getElementById('editPrice').value);
        else data.total_price = parseFloat(document.getElementById('editPrice').value);
        const endpoint = type === 'purchase' ? 'purchases' : 'sales';
        const response = await fetch(`${API_BASE}/${endpoint}/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
            credentials: 'include'
        });
        if (response.status === 401) {
            showAuthModal();
            return;
        }
        if (response.ok) {
            showAlert('stockAlert', 'Stock updated successfully!', 'success');
            closeEditModal();
            loadStockData(currentStockTab);
        } else {
            throw new Error('Failed to update stock');
        }
    } catch (error) {
        showAlert('stockAlert', 'Error updating stock: ' + error.message, 'error');
    } finally {
        showLoading('stockLoading', false);
    }
});

function chooseStockType(type) {
    currentStockTab = type;
    document.getElementById('stockTypeChoice').style.display = 'none';
    if (type === 'purchase') {
        document.getElementById('purchaseForm').style.display = 'block';
        document.getElementById('saleForm').style.display = 'none';
        document.getElementById('stockListTitle').textContent = 'Purchase Transactions';
        loadStockData('purchase');
    } else {
        document.getElementById('purchaseForm').style.display = 'none';
        document.getElementById('saleForm').style.display = 'block';
        document.getElementById('stockListTitle').textContent = 'Sale Transactions';
        loadStockData('sale');
    }
}

function resetStockType() {
    currentStockTab = 'all';
    document.getElementById('stockTypeChoice').style.display = 'flex';
    document.getElementById('purchaseForm').style.display = 'none';
    document.getElementById('saleForm').style.display = 'none';
    document.getElementById('stockListTitle').textContent = 'Recent Transactions';
    loadStockData('all');
}

const profileAvatar = document.getElementById('profileAvatar');
const profileDropdown = document.getElementById('profileDropdown');
const dropdownUsername = document.getElementById('dropdownUsername');

// Show dropdown on click
profileAvatar.addEventListener('click', function(e) {
    e.stopPropagation();
    if (currentVendor && currentVendor.Name) {
        dropdownUsername.textContent = currentVendor.Name;
    } else {
        dropdownUsername.textContent = 'User';
    }
    profileDropdown.style.display = profileDropdown.style.display === 'block' ? 'none' : 'block';
});

// Show dropdown on hover
profileAvatar.addEventListener('mouseenter', function() {
    if (currentVendor && currentVendor.Name) {
        dropdownUsername.textContent = currentVendor.Name;
    } else {
        dropdownUsername.textContent = 'User';
    }
    profileDropdown.style.display = 'block';
});

// Hide dropdown when mouse leaves the dropdown area
let hideDropdownTimeout;
profileAvatar.addEventListener('mouseleave', function() {
    hideDropdownTimeout = setTimeout(() => {
        profileDropdown.style.display = 'none';
    }, 300);
});

profileDropdown.addEventListener('mouseenter', function() {
    clearTimeout(hideDropdownTimeout);
});

profileDropdown.addEventListener('mouseleave', function() {
    profileDropdown.style.display = 'none';
});

document.addEventListener('click', function() {
    profileDropdown.style.display = 'none';
});

function openProfileModal() {
    if (!currentVendor) {
        showAlert('profileAlert', 'Please log in to edit profile.', 'error');
        showAuthModal();
        return;
    }
    profileDropdown.style.display = 'none';
    document.getElementById('profileName').value = currentVendor.Name || '';
    document.getElementById('profilePhone').value = currentVendor.PhoneNumber || '';
    document.getElementById('profileAddress').value = currentVendor.Location || '';
    document.getElementById('profileModal').style.display = 'flex';
}

function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

document.getElementById('profileForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!currentVendor || !currentVendor.id) {
        showAlert('profileAlert', 'Error: No vendor logged in. Please log in again.', 'error');
        showAuthModal();
        return;
    }
    const name = document.getElementById('profileName').value;
    const phone_number = document.getElementById('profilePhone').value;
    const address = document.getElementById('profileAddress').value;
    try {
        const response = await fetch(`${API_BASE}/vendor/${currentVendor.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                Name: name, 
                PhoneNumber: phone_number, 
                Location: address,
                BusinessInfo: currentVendor.BusinessInfo || ''
            }),
            credentials: 'include'
        });
        if (response.status === 401) {
            showAlert('profileAlert', 'Session expired. Please log in again.', 'error');
            showAuthModal();
            return;
        }
        if (response.ok) {
            currentVendor = await response.json();
            localStorage.setItem('currentVendor', JSON.stringify(currentVendor));
            showAlert('profileAlert', 'Profile updated!', 'success');
            setTimeout(() => {
                closeProfileModal();
                document.getElementById('profileAlert').innerHTML = '';
                updateProfileDisplay();
                document.getElementById('phoneNumber').value = currentVendor.PhoneNumber || '';
            }, 1200);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to update profile (Status: ${response.status})`);
        }
    } catch (err) {
        console.error('Profile update error:', err);
        showAlert('profileAlert', `Failed to update profile: ${err.message}`, 'error');
    }
});

window.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
});

function checkAuthentication() {
    const storedVendor = localStorage.getItem('currentVendor');
    if (storedVendor) {
        currentVendor = JSON.parse(storedVendor);
        console.log('Vendor loaded from localStorage:', currentVendor);
        hideAuthModal();
        updateProfileDisplay();
        loadVendorDetails(); // Load full vendor details after authentication
        loadSectionData(document.querySelector('.content-section.active').id);
        return;
    }
    const urlParams = new URLSearchParams(window.location.search);
    const phoneNumber = urlParams.get('phone_number');
    if (phoneNumber) {
        autoCheckPhoneNumber(phoneNumber);
    } else {
        showAuthModal();
    }
}

async function autoCheckPhoneNumber(phoneNumber) {
    console.log('Auto-checking phone number:', phoneNumber);
    try {
        const response = await fetch(`${API_BASE}/vendor/authenticate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `phone_number=${encodeURIComponent(phoneNumber)}`,
            credentials: 'include'
        });
        if (response.ok) {
            const result = await response.json();
            console.log('Authentication response:', result);
            if (result && 'exists' in result) {
                if (result.exists) {
                    currentVendor = result.vendor;
                    localStorage.setItem('currentVendor', JSON.stringify(currentVendor));
                    hideAuthModal();
                    updateProfileDisplay();
                    loadVendorDetails(); // Load full vendor details after authentication
                    loadSectionData(document.querySelector('.content-section.active').id);
                } else {
                    showRegisterStep(phoneNumber);
                }
            } else {
                console.error('Invalid response format');
                showAuthModal();
            }
        } else {
            console.error('Server error:', response.status);
            showAuthModal();
        }
    } catch (error) {
        console.error('Network error during auto-check:', error);
        showAuthModal();
    }
}

function showAuthModal() {
    console.log('Showing auth modal');
    document.getElementById('authModal').style.display = 'flex';
}

function hideAuthModal() {
    console.log('Hiding auth modal');
    document.getElementById('authModal').style.display = 'none';
}

function showLoginStep() {
    console.log('Switching to login step');
    document.getElementById('loginStep').style.display = 'block';
    document.getElementById('registerStep').style.display = 'none';
    document.getElementById('loginAlert').innerHTML = '';
}

function showRegisterStep(phoneNumber) {
    console.log('Switching to register step with phone:', phoneNumber);
    document.getElementById('loginStep').style.display = 'none';
    document.getElementById('registerStep').style.display = 'block';
    document.getElementById('regPhone').value = phoneNumber;
    document.getElementById('registrationAlert').innerHTML = '';
}

function updateProfileDisplay() {
    if (currentVendor) {
        console.log('Updating profile display for:', currentVendor.Name);
        let tooltip = document.getElementById('usernameTooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'usernameTooltip';
            document.getElementById('profileAvatar').appendChild(tooltip);
        }
        tooltip.textContent = currentVendor.Name;
        document.getElementById('phoneNumber').value = currentVendor.PhoneNumber || '';
        document.getElementById('profileName').value = currentVendor.Name || '';
        document.getElementById('profilePhone').value = currentVendor.PhoneNumber || '';
        document.getElementById('profileAddress').value = currentVendor.Location || '';
    } else {
        const tooltip = document.getElementById('usernameTooltip');
        if (tooltip) tooltip.remove();
    }
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const phoneNumber = document.getElementById('loginPhone').value;
    console.log('Login attempt with phone:', phoneNumber);
    try {
        const response = await fetch(`${API_BASE}/vendor/authenticate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `phone_number=${encodeURIComponent(phoneNumber)}`,
            credentials: 'include'
        });
        if (response.ok) {
            try {
                const result = await response.json();
                console.log('Login response:', result);
                if (result && 'exists' in result) {
                    if (result.exists) {
                        currentVendor = result.vendor;
                        localStorage.setItem('currentVendor', JSON.stringify(currentVendor));
                        document.getElementById('loginAlert').innerHTML = '<div style="color: green; text-align: center;">Welcome back, ' + currentVendor.Name + '!</div>';
                        setTimeout(() => {
                            hideAuthModal();
                            updateProfileDisplay();
                            loadVendorDetails();
                            loadSectionData(document.querySelector('.content-section.active').id);
                        }, 1500);
                    } else {
                        showRegisterStep(phoneNumber);
                    }
                } else {
                    console.error('Invalid response format');
                    document.getElementById('loginAlert').innerHTML = '<div style="color: red; text-align: center;">Invalid server response.</div>';
                }
            } catch (jsonError) {
                console.error('JSON parse error:', jsonError);
                document.getElementById('loginAlert').innerHTML = '<div style="color: red; text-align: center;">Invalid server response.</div>';
            }
        } else {
            console.error('Authentication failed:', response.status);
            document.getElementById('loginAlert').innerHTML = '<div style="color: red; text-align: center;">Error checking phone number. Please try again.</div>';
        }
    } catch (error) {
        console.error('Network error during login:', error);
        document.getElementById('loginAlert').innerHTML = '<div style="color: red; text-align: center;">Network error. Please try again.</div>';
    }
});

document.getElementById('authRegistrationForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const phone_number = document.getElementById('regPhone').value;
    const address = document.getElementById('regAddress').value;
    const business_info = document.getElementById('regBusiness').value;
    console.log('Registration attempt:', { name, phone_number });
    try {
        const response = await fetch(`${API_BASE}/vendor/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                Name: name,
                PhoneNumber: phone_number,
                Location: address,
                BusinessInfo: business_info
            }),
            credentials: 'include'
        });
        if (response.ok) {
            const vendor = await response.json();
            currentVendor = vendor;
            localStorage.setItem('currentVendor', JSON.stringify(vendor));
            document.getElementById('registrationAlert').innerHTML = '<div style="color: green; text-align: center;">Registration successful! Welcome, ' + vendor.Name + '!</div>';
            setTimeout(() => {
                hideAuthModal();
                updateProfileDisplay();
                loadVendorDetails();
                loadSectionData(document.querySelector('.content-section.active').id);
            }, 1500);
        } else {
            const error = await response.json();
            console.error('Registration failed:', error);
            document.getElementById('registrationAlert').innerHTML = '<div style="color: red; text-align: center;">Registration failed: ' + (error.detail || 'Unknown error') + '</div>';
        }
    } catch (error) {
        console.error('Network error during registration:', error);
        document.getElementById('registrationAlert').innerHTML = '<div style="color: red; text-align: center;">Network error. Please try again.</div>';
    }
});

// Add event listener for purchase form
document.getElementById('purchaseFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to add purchases.', 'error');
        showAuthModal();
        return;
    }
    
    showLoading('stockLoading', true);
    
    const itemName = document.getElementById('purchaseItemName').value.trim();
    const quantity = parseInt(document.getElementById('purchaseQuantity').value);
    const price = parseFloat(document.getElementById('purchasePrice').value);
    const paymentMethod = document.getElementById('purchasePaymentMethod').value;
    
    if (!itemName || isNaN(quantity) || quantity <= 0 || isNaN(price) || price <= 0 || !paymentMethod) {
        showAlert('stockAlert', 'Please fill all fields with valid values.', 'error');
        showLoading('stockLoading', false);
        return;
    }
    
    const payload = {
        item_name: itemName,
        quantity: quantity,
        price: price,
        payment_method: paymentMethod
    };
    
    try {
        const response = await fetch(`${API_BASE}/purchases/`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to add purchase: ${response.status} - ${errorText}`);
        }
        
        showAlert('stockAlert', 'Purchase added successfully!', 'success');
        document.getElementById('purchaseFormElement').reset();
        loadStockData(currentStockTab);
    } catch (error) {
        console.error('Error adding purchase:', error);
        showAlert('stockAlert', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('stockLoading', false);
    }
});

// Add event listener for sale form
document.getElementById('saleFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!currentVendor) {
        showAlert('stockAlert', 'Please log in to add sales.', 'error');
        showAuthModal();
        return;
    }
    
    showLoading('stockLoading', true);
    
    const itemName = document.getElementById('saleItemName').value.trim();
    const quantity = parseInt(document.getElementById('saleQuantity').value);
    const totalPrice = parseFloat(document.getElementById('saleTotalPrice').value);
    const paymentMethod = document.getElementById('salePaymentMethod').value;
    
    if (!itemName || isNaN(quantity) || quantity <= 0 || isNaN(totalPrice) || totalPrice <= 0 || !paymentMethod) {
        showAlert('stockAlert', 'Please fill all fields with valid values.', 'error');
        showLoading('stockLoading', false);
        return;
    }
    
    const payload = {
        item_name: itemName,
        quantity: quantity,
        total_price: totalPrice,
        payment_method: paymentMethod
    };
    
    try {
        const response = await fetch(`${API_BASE}/sales/`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to add sale: ${response.status} - ${errorText}`);
        }
        
        showAlert('stockAlert', 'Sale added successfully!', 'success');
        document.getElementById('saleFormElement').reset();
        loadStockData(currentStockTab);
    } catch (error) {
        console.error('Error adding sale:', error);
        showAlert('stockAlert', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('stockLoading', false);
    }
});