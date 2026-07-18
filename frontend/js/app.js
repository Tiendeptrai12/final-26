/* eslint-disable */
/**
 * Smart Assistant - Trợ Lý Mua Sắm Thông Thái (JS Engine Nâng Cấp Toàn Diện)
 * Bộ điều phối hội thoại thông minh tích hợp bộ trích xuất thực thể (Slot-Filling)
 * Hoàn toàn không cắt xén logic - Sẵn sàng chạy Production Mockup
 */

const MOCK_CATALOG = {
  ac: [
    {
      id: 'ac-pana-01',
      name: 'Panasonic Inverter 1 HP CU/CS-XPU9XKH-8',
      price: 11490000,
      brand: 'Panasonic',
      room_size: 'Dưới 15m²',
      noise: '19dB - siêu êm',
      inverter: true,
      stock: 12,
    },
    {
      id: 'ac-daikin-02',
      name: 'Daikin Inverter 1.5 HP FTKB35WAVMV',
      price: 13990000,
      brand: 'Daikin',
      room_size: 'Từ 15 đến 20m²',
      noise: '22dB - rất yên tĩnh',
      inverter: true,
      stock: 8,
    },
    {
      id: 'ac-casper-03',
      name: 'Casper Inverter 1 HP TC-09IS35',
      price: 5890000,
      brand: 'Casper',
      room_size: 'Dưới 15m²',
      noise: '28dB - trung bình',
      inverter: true,
      stock: 25,
    }
  ],
  fridge: [
    {
      id: 'fridge-samsung-01',
      name: 'Tủ lạnh Samsung Inverter 236 lít RT22M4032BY/SV',
      price: 6490000,
      brand: 'Samsung',
      liters: 236,
      family_size: '2 - 4 người',
      cooling: 'Chế độ đông mềm Optimal Fresh Zone tiện lợi',
      stock: 5,
    },
    {
      id: 'fridge-lg-02',
      name: 'Tủ lạnh LG Inverter 315 lít GN-D312PS',
      price: 8890000,
      brand: 'LG',
      liters: 315,
      family_size: '3 - 5 người',
      cooling: 'Hệ thống làm lạnh đa chiều Door Cooling tỏa đều',
      stock: 15,
    },
    {
      id: 'fridge-aqua-03',
      name: 'Tủ lạnh Aqua 90 lít AQR-D99FA',
      price: 2790000,
      brand: 'Aqua',
      liters: 90,
      family_size: '1 - 2 người (Sinh viên)',
      cooling: 'Làm lạnh trực tiếp bằng mạch khí cơ bản',
      stock: 4,
    }
  ],
  laptop: [
    {
      id: 'laptop-hp-01',
      name: 'HP Pavilion 14-dv2073TU (Core i5 / 8GB RAM / 512GB SSD)',
      price: 14500000,
      brand: 'HP',
      weight: '1.4kg',
      screen: '14 inch Full HD',
      stock: 9,
    },
    {
      id: 'laptop-asus-02',
      name: 'Asus Vivobook 14 OLED (Core i5 / 8GB RAM / 512GB SSD)',
      price: 15200000,
      brand: 'Asus',
      weight: '1.6kg',
      screen: '14 inch OLED siêu sắc nét',
      stock: 14,
    },
    {
      id: 'laptop-lenovo-03',
      name: 'Lenovo IdeaPad Slim 3 (Core i5 / 16GB RAM / 512GB SSD)',
      price: 12900000,
      brand: 'Lenovo',
      weight: '1.43kg',
      screen: '14 inch viền mỏng',
      stock: 22,
    }
  ]
};

const MOCK_PROMOTIONS = {
  installment_0: ['ac-pana-01', 'ac-daikin-02', 'fridge-lg-02'],
  discounts: {
    'ac-pana-01': 'Tặng combo ống đồng vật tư 800.000đ',
    'laptop-asus-02': 'Tặng chuột không dây Bluetooth chính hãng',
    'fridge-lg-02': 'Phiếu mua hàng gia dụng trị giá 300.000đ',
  }
};

const MOCK_FAQ = {
  'bảo hành': 'Dạ, sản phẩm tại Điện Máy Xanh được bảo hành chính hãng 1 đổi 1 trong vòng 30 ngày đầu nếu có lỗi phần cứng từ nhà sản xuất ạ!',
  'giao hàng': 'Dạ, hệ thống miễn phí vận chuyển lắp đặt trong bán kính 10km quanh siêu thị gần nhất ngay trong ngày ạ.',
  'trả góp': 'Dạ, hiện tại có chương trình hỗ trợ trả góp 0% lãi suất qua căn cước công dân gắn chip cực nhanh chóng, xét duyệt chỉ 5 phút ạ.'
};

// Cấu trúc quản lý trạng thái ứng dụng nâng cao (Slot-Filling State)
let sessionState = {
  stage: 'INIT', // INIT -> PROBING -> RECOMMENDATION
  category: null, // ac, fridge, laptop
  collectedData: {
    brand: null,
    budget: null, // { modifier: 'dưới'|'trên'|'tầm', value: số }
    roomSize: null, // số m2
    familySize: null, // số thành viên
    purpose: null // học tập, gaming...
  },
};

let consumerChatSessions = [];
let activeSessionId = null;

// ==========================================
// HỆ THỐNG ĐIỀU KHIỂN ĐÓNG/MỞ SIDEBAR
// ==========================================
function initCollapsibleSidebarLogic() {
  const sidebarPanel = document.getElementById('sidebar-panel');
  const btnClose = document.getElementById('btn-close-sidebar');
  const btnOpen = document.getElementById('btn-open-sidebar');

  if (!sidebarPanel || !btnClose || !btnOpen) return;

  btnClose.addEventListener('click', () => {
    sidebarPanel.classList.remove('w-80', 'p-5', 'border-r');
    sidebarPanel.classList.add('w-0', 'p-0', 'border-r-0', 'opacity-0', 'pointer-events-none');
    btnOpen.classList.remove('hidden');
  });

  btnOpen.addEventListener('click', () => {
    sidebarPanel.classList.remove('w-0', 'p-0', 'border-r-0', 'opacity-0', 'pointer-events-none');
    sidebarPanel.classList.add('w-80', 'p-5', 'border-r');
    btnOpen.classList.add('hidden');
  });
}

// ==========================================
// HIỆU ỨNG RUNG LẮC ĐỒNG LOẠT CHO TOÀN BỘ MASCOT
// ==========================================
function injectJiggleStyles() {
  if (document.getElementById('mascot-jiggle-style')) return;
  const style = document.createElement('style');
  style.id = 'mascot-jiggle-style';
  style.innerHTML = `
    @keyframes jiggleVivid {
      0% { transform: scale(1) rotate(0deg); }
      15% { transform: scale(1.15) rotate(-10deg); }
      30% { transform: scale(1.15) rotate(8deg); }
      45% { transform: scale(1.08) rotate(-6deg); }
      60% { transform: scale(1.08) rotate(4deg); }
      75% { transform: scale(1.02) rotate(-2deg); }
      100% { transform: scale(1) rotate(0deg); }
    }
    .animate-jiggle-vivid {
      animation: jiggleVivid 0.6s ease-in-out;
      display: inline-block !important;
    }
  `;
  document.head.appendChild(style);
}

function triggerMascotJiggle() {
  const allMascots = document.querySelectorAll('img[src*="mascot"]');
  allMascots.forEach(mascot => {
    mascot.classList.add('animate-jiggle-vivid');
  });
  setTimeout(() => {
    allMascots.forEach(mascot => {
      mascot.classList.remove('animate-jiggle-vivid');
    });
  }, 600);
}

// Advisor scope: no order/shipping/payment handling here. Send users to the real
// dienmayxanh.com product/search page for those steps; `product.url` wins when the
// backend supplies a real product page, else fall back to a site search by name.
function dmxProductLink(product) {
  if (product && product.url) return product.url;
  const q = encodeURIComponent((product && product.name) || '');
  return `https://www.dienmayxanh.com/tim-kiem?key=${q}`;
}

// ==========================================
// UTILITIES & CHAT UI RENDERERS
// ==========================================
function formatVND(amount) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount).replace('₫', 'đ');
}

function scrollChatToBottom() {
  const chatBox = document.getElementById('chat-box');
  if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

function showTypingIndicator() {
  const chatBox = document.getElementById('chat-box');
  if (!chatBox) return;
  const html = `
    <div id="typing-indicator" class="flex items-start space-x-3.5 message-fade-in">
      <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 dark:border-brand-border flex items-center justify-center overflow-hidden shrink-0 shadow-md">
        <img src="img/mascot.png" alt="..." class="w-full h-full object-contain p-0.5 animate-pulse" onerror="this.src='https://placehold.co/100x100?text=Mascot'">
      </div>
      <div class="glass-message-card text-slate-400 rounded-2xl rounded-tl-none px-4 py-3 border border-slate-200 dark:border-brand-border">
        <div class="flex items-center space-x-1 py-1">
          <span class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
          <span class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
          <span class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
        </div>
      </div>
    </div>`;
  chatBox.insertAdjacentHTML('beforeend', html);
  scrollChatToBottom();
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

function appendUserMessage(text) {
  const chatBox = document.getElementById('chat-box');
  if (!chatBox) return;
  const html = `
    <div class="flex items-start space-x-3 justify-end message-fade-in">
      <div class="space-y-1 max-w-[80%]">
        <div class="bg-gradient-to-r from-[#1d4ed8] to-[#0095da] text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-md">
          <p class="text-sm leading-relaxed">${text}</p>
        </div>
      </div>
      <div class="w-9 h-9 rounded-xl bg-white dark:bg-brand-panel border border-slate-200 dark:border-brand-border flex items-center justify-center shrink-0 shadow-sm">
        <i class="fa-solid fa-user text-brand-electric text-sm"></i>
      </div>
    </div>`;
  chatBox.insertAdjacentHTML('beforeend', html);
  scrollChatToBottom();

  if (activeSessionId) {
    const s = consumerChatSessions.find(item => item.id === activeSessionId);
    if (s) s.messages.push({ role: 'user', content: text });
  }
}

function appendAssistantMessage(htmlContent) {
  const chatBox = document.getElementById('chat-box');
  if (!chatBox) return;
  const html = `
    <div class="flex items-start space-x-3.5 message-fade-in">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-white to-slate-100 border border-white flex items-center justify-center shrink-0 shadow-[0_4px_10px_rgba(0,149,218,0.15)] overflow-hidden">
        <img src="img/mascot.png" alt="Avatar" class="w-[85%] h-[85%] object-contain" onerror="this.src='https://placehold.co/100x100?text=AI'">
      </div>
      <div class="space-y-1 max-w-[85%] w-full">
        <div class="glass-message-card text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-none px-5 py-3.5 border border-white/50 dark:border-brand-border/40">
          ${htmlContent}
        </div>
      </div>
    </div>`;
  chatBox.insertAdjacentHTML('beforeend', html);
  scrollChatToBottom();

  if (activeSessionId) {
    const s = consumerChatSessions.find(item => item.id === activeSessionId);
    if (s) s.messages.push({ role: 'assistant', content: htmlContent });
  }
}
window.appendAssistantMessage = appendAssistantMessage;

// ==========================================
// QUẢN LÝ LỊCH SỬ PHIÊN TRÒ CHUYỆN (SESSIONS)
// ==========================================
function createNewChatSession(initialTitle = "Cuộc trò chuyện mới") {
  const newId = 'session_' + Date.now();
  const newSession = {
    id: newId,
    title: initialTitle,
    timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    messages: [],
    category: null
  };
  consumerChatSessions.unshift(newSession);
  activeSessionId = newId;
  renderChatHistoryUI();
  return newSession;
}

function updateActiveSessionTitle(newTitle, categoryCode) {
  if (!activeSessionId) return;
  const s = consumerChatSessions.find(item => item.id === activeSessionId);
  if (s) {
    s.title = newTitle;
    if (categoryCode) s.category = categoryCode;
    renderChatHistoryUI();
  }
}

function renderChatHistoryUI() {
  const container = document.getElementById('chat-history-list');
  if (!container) return;

  if (consumerChatSessions.length === 0) {
    container.innerHTML = `
      <div id="history-empty-state" class="text-center py-8 px-4 border border-dashed border-slate-200 dark:border-brand-border/40 rounded-xl">
        <p class="text-[11px] text-slate-400 italic">Chưa có cuộc trò chuyện cũ.</p>
      </div>`;
    return;
  }

  container.innerHTML = '';
  consumerChatSessions.forEach(session => {
    const isActive = session.id === activeSessionId;
    const pill = document.createElement('div');

    pill.className = `group flex items-center justify-between p-3 rounded-xl border transition-all duration-200 cursor-pointer text-xs font-medium history-item-appear ${
      isActive
      ? 'border-brand-electric/40 bg-brand-electric/5 text-brand-electric dark:bg-brand-electric/10'
      : 'border-slate-100 dark:border-brand-border/40 bg-slate-50/60 dark:bg-brand-panel/40 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-brand-dark/30'
    }`;

    let icon = '<i class="fa-regular fa-comment text-slate-400"></i>';
    if (session.category === 'ac') icon = '<i class="fa-solid fa-snowflake text-cyan-500"></i>';
    if (session.category === 'fridge') icon = '<i class="fa-solid fa-carrot text-emerald-500"></i>';
    if (session.category === 'laptop') icon = '<i class="fa-solid fa-laptop text-indigo-500"></i>';

    pill.innerHTML = `
      <div class="flex items-center space-x-2.5 truncate w-[90%]">
        <span class="shrink-0 text-sm">${icon}</span>
        <div class="truncate flex flex-col text-left">
          <span class="truncate font-semibold text-slate-900 dark:text-slate-100">${session.title}</span>
          <span class="text-[10px] text-slate-400 mt-0.5">${session.timestamp} • Điện Máy Xanh</span>
        </div>
      </div>`;

    pill.addEventListener('click', () => {
      activeSessionId = session.id;
      renderChatHistoryUI();
      restoreSessionMessages(session);
    });
    container.appendChild(pill);
  });
}

function restoreSessionMessages(session) {
  const chatBox = document.getElementById('chat-box');
  if (!chatBox) return;

  if (!session.messages || session.messages.length === 0) {
    chatBox.innerHTML = `
      <div class="flex items-start space-x-3.5 message-fade-in">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-white to-slate-100 border border-white flex items-center justify-center overflow-hidden shrink-0 shadow-[0_4px_10px_rgba(0,149,218,0.15)] bg-white">
          <img src="img/mascot.png" alt="Avatar" class="w-[85%] h-[85%] object-contain" onerror="this.src='https://placehold.co/100x100?text=AI'">
        </div>
        <div class="space-y-1 max-w-[85%] w-full">
          <div class="glass-message-card text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-none px-5 py-3.5 border border-white/50 dark:border-brand-border/40">
            <p class="text-sm">Dạ, phiên hội thoại tư vấn mua sắm mới đã sẵn sàng phục vụ rồi ạ!</p>
          </div>
        </div>
      </div>`;
    sessionState.stage = 'INIT';
    sessionState.category = null;
    sessionState.collectedData = { brand: null, budget: null, roomSize: null, familySize: null, purpose: null };

    document.getElementById('active-category').textContent = 'Chưa xác định';
    document.getElementById('chat-stage').textContent = 'INIT';
    scrollChatToBottom();
    return;
  }

  chatBox.innerHTML = '';
  session.messages.forEach(msg => {
    if (msg.role === 'user') {
      const html = `<div class="flex items-start space-x-3 justify-end message-fade-in"><div class="max-w-[80%] bg-gradient-to-r from-[#1d4ed8] to-[#0095da] text-white rounded-2xl rounded-tr-none px-4 py-3 text-[13.5px] shadow-sm">${msg.content}</div></div>`;
      chatBox.insertAdjacentHTML('beforeend', html);
    } else {
      const html = `<div class="flex items-start space-x-3.5 message-fade-in"><div class="w-10 h-10 rounded-xl bg-white border border-white flex items-center justify-center shrink-0 shadow-[0_4px_10px_rgba(0,149,218,0.15)] overflow-hidden"><img src="img/mascot.png" class="w-[85%] h-[85%] object-contain"></div><div class="max-w-[85%] w-full glass-message-card text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-none px-5 py-3.5 text-[13.5px]">${msg.content}</div></div>`;
      chatBox.insertAdjacentHTML('beforeend', html);
    }
  });

  sessionState.category = session.category;
  sessionState.stage = session.messages.length > 0 ? 'RECOMMENDATION' : 'INIT';
  document.getElementById('active-category').textContent = session.category || 'Chưa xác định';
  document.getElementById('chat-stage').textContent = sessionState.stage;
  scrollChatToBottom();
}

// ========================================================
// HEURISTIC NLP PARSER - TRÍCH XUẤT THÔNG TIN TỰ NHIÊN TIẾNG VIỆT
// ========================================================
function extractEntitiesFromText(text) {
  const lower = text.toLowerCase();
  let result = {};

  // 1. Phân loại nhóm ngành hàng (Category)
  if (lower.includes('máy lạnh') || lower.includes('điều hòa') || lower.includes('đh')) {
    result.category = 'ac';
  } else if (lower.includes('tủ lạnh') || lower.includes('tl')) {
    result.category = 'fridge';
  } else if (lower.includes('laptop') || lower.includes('máy tính')) {
    result.category = 'laptop';
  }

  // 2. Trích xuất Hãng sản xuất (Brand)
  const brandsList = ['panasonic', 'daikin', 'casper', 'samsung', 'lg', 'aqua', 'hp', 'asus', 'lenovo'];
  for (const b of brandsList) {
    if (lower.includes(b)) {
      result.brand = b.charAt(0).toUpperCase() + b.slice(1);
      break;
    }
  }
  if (!result.brand && lower.includes('pana')) result.brand = 'Panasonic';

  // 3. Trích xuất hạn mức tài chính (Budget) - Ví dụ: "dưới 15 củ", "tầm 10tr", "khoảng 8 triệu"
  const priceRegex = /(dưới|trên|tầm|khoảng|~)?\s*(\d+)\s*(triệu|tr|củ)/i;
  const matchPrice = lower.match(priceRegex);
  if (matchPrice) {
    const modifier = matchPrice[1] || 'tầm';
    const numericValue = parseInt(matchPrice[2], 10) * 1000000;
    result.budget = { modifier, value: numericValue };
  }

  // 4. Trích xuất diện tích phòng cho Máy Lạnh (Room Size)
  const roomRegex = /(\d+)\s*(m2|m²)/i;
  const matchRoom = lower.match(roomRegex);
  if (matchRoom) {
    result.roomSize = parseInt(matchRoom[1], 10);
  } else if (lower.includes('phòng ngủ')) {
    result.roomSize = 12; // Mức mặc định phòng ngủ phổ thông
  } else if (lower.includes('phòng khách')) {
    result.roomSize = 22; // Mức mặc định phòng khách phổ thông
  }

  // 5. Trích xuất số người dùng cho Tủ Lạnh (Family Size)
  const familyRegex = /(\d+)\s*(người|thành viên|nhân khẩu)/i;
  const matchFamily = lower.match(familyRegex);
  if (matchFamily) {
    result.familySize = parseInt(matchFamily[1], 10);
  } else if (lower.includes('sinh viên') || lower.includes('ở một mình') || lower.includes('trọ')) {
    result.familySize = 1;
  }

  // 6. Trích xuất nhu cầu laptop (Purpose)
  if (lower.includes('sinh viên') || lower.includes('học tập') || lower.includes('văn phòng') || lower.includes('mỏng nhẹ')) {
    result.purpose = 'office';
  } else if (lower.includes('gaming') || lower.includes('đồ họa') || lower.includes('chơi game')) {
    result.purpose = 'heavy';
  }

  return result;
}

// ========================================================
// CORE LOGIC ENGINE - ĐIỀU PHỐI HỘI THOẠI & DỮ LIỆU RAG
// ========================================================
function handleFormSubmit(event) {
  event.preventDefault();
  const input = document.getElementById('user-input');
  if (!input) return;
  const val = input.value.trim();
  if (!val) return;

  if (!activeSessionId) createNewChatSession();

  appendUserMessage(val);
  input.value = '';
  showTypingIndicator();

  setTimeout(() => {
    removeTypingIndicator();
    dispatchLogicEngine(val);
  }, 600);
}

function dispatchLogicEngine(text) {
  const startTime = performance.now();
  const lower = text.toLowerCase();

  // BƯỚC 1: QUÉT FAQ ĐỒNG BỘ (Bảo hành, giao hàng, trả góp)
  for (const [key, answer] of Object.entries(MOCK_FAQ)) {
    if (lower.includes(key)) {
      document.getElementById('rag-faq-status').textContent = `Khớp FAQ: [${key}]`;
      document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
      appendAssistantMessage(`<p class="text-sm"><i class="fa-solid fa-circle-info text-brand-electric mr-1.5"></i>${answer}</p>`);
      return;
    }
  }
  document.getElementById('rag-faq-status').textContent = 'Không khớp FAQ';

  // BƯỚC 2: NLP TRÍCH XUẤT THỰC THỂ (SLOT-FILLING)
  const extracted = extractEntitiesFromText(text);

  // Hợp nhất các slot dữ liệu tìm được vào sessionState hiện hành
  if (extracted.category) sessionState.category = extracted.category;
  if (extracted.brand) sessionState.collectedData.brand = extracted.brand;
  if (extracted.budget) sessionState.collectedData.budget = extracted.budget;
  if (extracted.roomSize) sessionState.collectedData.roomSize = extracted.roomSize;
  if (extracted.familySize) sessionState.collectedData.familySize = extracted.familySize;
  if (extracted.purpose) sessionState.collectedData.purpose = extracted.purpose;

  // Cập nhật giao diện gỡ lỗi (Hộp đen ẩn) trực quan theo DOM
  document.getElementById('active-category').textContent = sessionState.category || 'Chưa xác định';
  document.getElementById('slang-inspector').textContent = JSON.stringify(sessionState.collectedData);

  // BƯỚC 3: KIỂM TRA TÍNH XÁC ĐỊNH NGÀNH HÀNG (CATEGORY PROBING)
  if (!sessionState.category) {
    sessionState.stage = 'INIT';
    document.getElementById('chat-stage').textContent = sessionState.stage;
    document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
    appendAssistantMessage('<p class="text-sm">Dạ, em có thể hỗ trợ tư vấn chuyên sâu và so sánh thông thái về 3 nhóm sản phẩm: <strong>Máy lạnh, Tủ lạnh, hoặc Laptop</strong>. Anh/chị đang có nhu cầu tìm mua sản phẩm nào ạ?</p>');
    return;
  }

  // Đồng bộ tiêu đề Sidebar dựa trên Ngành hàng được khóa
  let categoryLabel = "Trò chuyện";
  if (sessionState.category === 'ac') categoryLabel = "Tư vấn Máy Lạnh";
  if (sessionState.category === 'fridge') categoryLabel = "Tư vấn Tủ Lạnh";
  if (sessionState.category === 'laptop') categoryLabel = "Tư vấn Laptop";
  updateActiveSessionTitle(categoryLabel, sessionState.category);

  // BƯỚC 4: ĐIỀU TRA THÔNG TIN CÒN THIẾU DỰA TRÊN NGÀNH HÀNG (DYNAMIC SLOT PROBING)

  // A. Nếu là Máy Lạnh mà chưa biết không gian / diện tích lắp đặt
  if (sessionState.category === 'ac' && !sessionState.collectedData.roomSize) {
    if (sessionState.stage === 'PROBING') {
      // Người dùng đã được hỏi câu này ở lượt trước nhưng nhập text tự do không có số m2 cụ thể -> Áp dụng Default Fallback thông minh
      sessionState.collectedData.roomSize = 12;
      appendAssistantMessage('<p class="text-xs italic text-slate-400 mb-2"><i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Em xin phép lấy mức diện tích phòng ngủ tiêu chuẩn phổ thông (dưới 15m²) để lọc sản phẩm ngay cho mình nhé.</p>');
    } else {
      sessionState.stage = 'PROBING';
      document.getElementById('chat-stage').textContent = sessionState.stage;
      document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
      appendAssistantMessage('<p class="text-sm">Dạ, để em tính toán công suất số Ngựa (HP) tối ưu nhất, anh/chị cho em hỏi <strong>diện tích phòng lắp đặt khoảng bao nhiêu m²</strong> (hoặc lắp cho không gian nào như phòng ngủ, phòng khách) ạ?</p>');
      return;
    }
  }

  // B. Nếu là Tủ Lạnh mà chưa biết nhu cầu thành viên sử dụng
  if (sessionState.category === 'fridge' && !sessionState.collectedData.familySize) {
    if (sessionState.stage === 'PROBING') {
      // Fallback khi người dùng nhập dữ liệu text tự do không chứa số lượng
      sessionState.collectedData.familySize = 3;
      appendAssistantMessage('<p class="text-xs italic text-slate-400 mb-2"><i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Em xin phép lấy dung tích tiêu chuẩn cho hộ gia đình 3 - 4 thành viên phổ biến để đề xuất các mẫu tối ưu nhé.</p>');
    } else {
      sessionState.stage = 'PROBING';
      document.getElementById('chat-stage').textContent = sessionState.stage;
      document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
      appendAssistantMessage('<p class="text-sm">Dạ, nhà mình dự kiến **có khoảng bao nhiêu thành viên** sẽ dùng chung tủ lạnh ạ, để em lọc mức dung tích (lít) chứa thực phẩm vừa vặn nhất cho gia đình mình?</p>');
      return;
    }
  }

  // C. Nếu là Laptop mà chưa biết phân khúc giá hoặc hãng, hỏi thêm để tăng tính gợi mở
  if (sessionState.category === 'laptop' && !sessionState.collectedData.brand && !sessionState.collectedData.budget) {
    if (sessionState.stage !== 'PROBING') {
      sessionState.stage = 'PROBING';
      document.getElementById('chat-stage').textContent = sessionState.stage;
      document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
      appendAssistantMessage('<p class="text-sm">Dạ, anh/chị tìm mua laptop phục vụ chính cho **nhu cầu học tập văn phòng mỏng nhẹ** hay **đồ họa chơi game nặng** ạ? Nếu mình có khoảng ngân sách dự kiến, hãy chia sẻ để em định hình máy chuẩn nhất nha!</p>');
      return;
    }
  }

  // BƯỚC 5: KHU VỰC TRUY VẤN DỮ LIỆU KHO HÀNG & PHÂN TÍCH TRADE-OFF (RECOMMENDATION ENGINE)
  sessionState.stage = 'RECOMMENDATION';
  document.getElementById('chat-stage').textContent = sessionState.stage;

  const catalog = MOCK_CATALOG[sessionState.category];
  let filteredProducts = [...catalog];

  // Thực hiện lọc theo Hãng sản xuất nếu có
  if (sessionState.collectedData.brand) {
    const targetBrand = sessionState.collectedData.brand.toLowerCase();
    filteredProducts = filteredProducts.filter(p => p.brand.toLowerCase().includes(targetBrand));
  }

  // Thực hiện lọc theo Hạn mức tài chính nếu có
  if (sessionState.collectedData.budget) {
    const { modifier, value } = sessionState.collectedData.budget;
    if (modifier === 'dưới') {
      filteredProducts = filteredProducts.filter(p => p.price <= value);
    } else if (modifier === 'trên') {
      filteredProducts = filteredProducts.filter(p => p.price >= value);
    } else { // tầm, khoảng, ~
      // Cho phép sai số biên rộng hơn 15% để tránh bộ lọc trống (Không làm mất cơ hội bán hàng)
      filteredProducts = filteredProducts.filter(p => p.price <= value * 1.15);
    }
  }

  // Thực hiện lọc theo Diện tích phòng (Đối với Máy lạnh)
  if (sessionState.category === 'ac' && sessionState.collectedData.roomSize) {
    const size = sessionState.collectedData.roomSize;
    if (size <= 15) {
      filteredProducts = filteredProducts.filter(p => p.room_size.includes('Dưới 15m²'));
    } else {
      filteredProducts = filteredProducts.filter(p => p.room_size.includes('15 đến 20m²'));
    }
  }

  // Thực hiện lọc theo Số lượng người dùng (Đối với Tủ lạnh)
  if (sessionState.category === 'fridge' && sessionState.collectedData.familySize) {
    const size = sessionState.collectedData.familySize;
    if (size <= 2) {
      filteredProducts = filteredProducts.filter(p => p.family_size.includes('1 - 2') || p.family_size.includes('2 - 4'));
    } else if (size >= 3 && size <= 4) {
      filteredProducts = filteredProducts.filter(p => p.family_size.includes('2 - 4') || p.family_size.includes('3 - 5'));
    } else {
      filteredProducts = filteredProducts.filter(p => p.family_size.includes('3 - 5'));
    }
  }

  // Nếu bộ lọc quá chặt dẫn đến không tìm thấy sản phẩm nào -> Fallback: Hiển thị toàn bộ danh mục kèm thông báo nới lỏng tiêu chí
  let isFallbackTriggered = false;
  if (filteredProducts.length === 0) {
    filteredProducts = [...catalog];
    isFallbackTriggered = true;
  }

  // Cập nhật trạng thái RAG gỡ lỗi trực quan lên DOM hộp ẩn
  document.getElementById('rag-catalog-status').textContent = `Tìm thấy ${filteredProducts.length} mẫu`;
  document.getElementById('rag-promo-status').textContent = 'Đã áp mã khuyến mãi dynamic';

  // Biện luận tiêu đề giới thiệu dựa trên kết quả lọc dữ liệu thật
  let introductionPrompt = "";
  if (isFallbackTriggered) {
    introductionPrompt = `Dạ hiện tại kho hàng không có mẫu nào khớp hoàn hảo 100% tiêu chí đặc thù trên, em xin phép đề xuất **Top ${filteredProducts.length} sản phẩm bán chạy nhất** thuộc nhóm ngành hàng này tại Điện Máy Xanh để anh/chị cân nhắc ạ:`;
  } else {
    introductionPrompt = `Dạ tuyệt vời! Khảo sát kho hàng thời gian thực, em đã tìm thấy **${filteredProducts.length} sản phẩm tối ưu nhất** phù hợp hoàn chỉnh với mong muốn của mình. Dưới đây là phân tích đặc tính kỹ thuật kèm điểm đánh đổi thực tế:`;
  }

  // Xây dựng chuỗi HTML thẻ sản phẩm lưới linh hoạt (Responsive Grid) phong cách thiết kế mới
  let cardsHtml = `<p class="text-[13.5px] leading-relaxed mb-4 text-slate-800 dark:text-slate-200">${introductionPrompt}</p>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">`;

  filteredProducts.forEach((product, idx) => {
    const hasZeroInstallment = MOCK_PROMOTIONS.installment_0.includes(product.id);
    const promotionGift = MOCK_PROMOTIONS.discounts[product.id] || 'Tặng phiếu mua hàng trị giá 200.000đ (Áp dụng mua đồ gia dụng)';

    // Biện luận Điểm đánh đổi (Trade-off) động dựa trên thuộc tính sản phẩm thật
    let tradeOffAnalysis = "Dòng sản phẩm quốc dân, lượng đặt mua rất cao dễ gặp tình trạng thiếu hàng cục bộ tại một số quận huyện.";
    if (product.price < 6000000) {
      tradeOffAnalysis = "Giá thành siêu rẻ tiết kiệm chi phí, tuy nhiên tính năng chỉ dừng ở mức cơ bản, không tích hợp nhiều công nghệ cảm biến cao cấp.";
    } else if (product.price > 13000000) {
      tradeOffAnalysis = "Công nghệ và độ bền xuất sắc hàng đầu, tuy nhiên tổng chi phí đầu tư ban đầu sẽ cao hơn các thương hiệu phổ thông.";
    }

    // Xử lý chuỗi thông số kỹ thuật đặc thù tương ứng từng ngành hàng
    let specsHtml = "";
    if (sessionState.category === 'ac') {
      specsHtml = `<li><i class="fa-solid fa-expand text-slate-400 mr-1.5"></i>Diện tích: <strong>${product.room_size}</strong></li>
                   <li><i class="fa-solid fa-volume-low text-slate-400 mr-1.5"></i>Độ ồn: <strong>${product.noise}</strong></li>`;
    } else if (sessionState.category === 'fridge') {
      specsHtml = `<li><i class="fa-solid fa-box-open text-slate-400 mr-1.5"></i>Dung tích: <strong>${product.liters} Lít</strong></li>
                   <li><i class="fa-solid fa-snowflake text-slate-400 mr-1.5"></i>Làm lạnh: <strong>${product.family_size}</strong></li>`;
    } else if (sessionState.category === 'laptop') {
      specsHtml = `<li><i class="fa-solid fa-weight-hanging text-slate-400 mr-1.5"></i>Trọng lượng: <strong>${product.weight}</strong></li>
                   <li><i class="fa-solid fa-laptop text-slate-400 mr-1.5"></i>Màn hình: <strong>${product.screen}</strong></li>`;
    }

    cardsHtml += `
      <div class="bg-white dark:bg-brand-panel/90 rounded-xl p-4 border border-slate-200 dark:border-brand-border flex flex-col justify-between space-y-3.5 shadow-sm transition-all hover:shadow-md hover:border-brand-electric/40">
        <div>
          <div class="flex items-center justify-between">
            <span class="px-2 py-0.5 text-[10px] font-bold bg-brand-electric/10 text-brand-electric rounded">Đề xuất ${idx + 1}</span>
            ${hasZeroInstallment ? `<span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded flex items-center gap-0.5"><i class="fa-solid fa-bolt text-[8px]"></i> Trả góp 0%</span>` : ''}
          </div>
          <h3 class="font-bold text-[12.5px] text-slate-900 dark:text-white mt-2 line-clamp-2 h-9 leading-snug">${product.name}</h3>
          <div class="text-[15px] font-extrabold text-blue-600 dark:text-brand-electric mt-1.5">${formatVND(product.price)}</div>

          <ul class="text-[11px] text-slate-600 dark:text-slate-400 mt-2.5 space-y-1 bg-slate-50 dark:bg-brand-dark/40 p-2.5 rounded-lg border border-slate-100 dark:border-brand-border/30">
            ${specsHtml}
          </ul>

          <p class="text-[11px] text-amber-700 dark:text-amber-400 font-semibold mt-2.5 flex items-start"><i class="fa-solid fa-gift mr-1.5 mt-0.5 text-xs shrink-0"></i><span>Quà tặng: ${promotionGift}</span></p>
        </div>

        <div class="bg-amber-500/5 dark:bg-amber-500/10 p-2.5 rounded-lg text-[11px] text-amber-800 dark:text-amber-400 border border-amber-500/20 leading-relaxed">
          <strong>Điểm đánh đổi (Trade-off):</strong> ${tradeOffAnalysis}
        </div>

        <a href="${dmxProductLink(product)}" target="_blank" rel="noopener noreferrer"
           class="w-full custom-btn-select text-xs py-2.5 rounded-xl font-bold transition-all shadow-sm flex items-center justify-center gap-1.5">
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>Xem tại Điện Máy Xanh
        </a>
      </div>`;
  });

  cardsHtml += `</div>`;
  appendAssistantMessage(cardsHtml);

  // Khôi phục chu trình máy trạng thái về trạng thái khởi tạo ban đầu chuẩn bị cho phiên lọc tiếp theo
  sessionState.stage = 'INIT';
  sessionState.category = null;
  sessionState.collectedData = { brand: null, budget: null, roomSize: null, familySize: null, purpose: null };

  document.getElementById('chat-stage').textContent = sessionState.stage;
  document.getElementById('latency-val').textContent = Math.round(performance.now() - startTime) + 'ms';
}

// ==========================================
// CÁC HÀM KHỞI TẠO VÀ LÀM MỚI PHIÊN (RESET/PROMPT)
// ==========================================
window.resetConversation = function() {
  if (activeSessionId) {
    const currentSession = consumerChatSessions.find(item => item.id === activeSessionId);
    if (currentSession && (!currentSession.messages || currentSession.messages.length === 0)) {
      return;
    }
  }

  const chatBox = document.getElementById('chat-box');
  if (chatBox) {
    chatBox.innerHTML = `
      <div class="flex items-start space-x-3.5 message-fade-in">
        <div class="w-10 h-10 rounded-xl bg-white border border-white flex items-center justify-center overflow-hidden shrink-0 shadow-[0_4px_10px_rgba(0,149,218,0.15)]">
          <img src="img/mascot.png" alt="Avatar" class="w-[85%] h-[85%] object-contain" onerror="this.src='https://placehold.co/100x100?text=AI'">
        </div>
        <div class="space-y-1 max-w-[85%] w-full">
          <div class="glass-message-card text-slate-800 dark:text-slate-200 rounded-2xl rounded-tl-none px-5 py-3.5 border border-white/50 dark:border-brand-border/40">
            <p class="text-sm">Dạ, phiên hội thoại tư vấn mua sắm mới đã sẵn sàng phục vụ rồi ạ! Anh/chị cần em hỗ trợ tìm kiếm dòng thiết bị công nghệ điện máy nào thế ạ?</p>
          </div>
        </div>
      </div>`;
  }

  sessionState.stage = 'INIT';
  sessionState.category = null;
  sessionState.collectedData = { brand: null, budget: null, roomSize: null, familySize: null, purpose: null };

  document.getElementById('active-category').textContent = 'Chưa xác định';
  document.getElementById('chat-stage').textContent = 'INIT';
  document.getElementById('slang-inspector').textContent = '';
  document.getElementById('rag-catalog-status').textContent = '';
  document.getElementById('rag-promo-status').textContent = '';
  document.getElementById('rag-faq-status').textContent = '';

  createNewChatSession();
};

window.fillQuickPrompt = function(promptText) {
  const input = document.getElementById('user-input');
  if (input) {
    input.value = promptText;
    input.focus();
  }
};

// ĐỒNG BỘ KHỞI TẠO KHI TẢI TRANG HOÀN TẤT
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chat-form');
  if (form) form.addEventListener('submit', handleFormSubmit);

  initCollapsibleSidebarLogic();
  injectJiggleStyles();

  // Ép cụm văn bản bảo mật căn lề trái chuẩn xác theo thiết kế đồ họa
  const allElements = document.getElementsByTagName('*');
  for (let el of allElements) {
    if (el.textContent.trim().startsWith('Dữ liệu bảo mật') && el.children.length === 0) {
      el.style.textAlign = 'left';
      el.style.display = 'block';
      if (el.parentElement) {
        el.parentElement.style.display = 'flex';
        el.parentElement.style.flexDirection = 'column';
        el.parentElement.style.alignItems = 'flex-start';
        el.parentElement.style.textAlign = 'left';
        el.parentElement.style.paddingLeft = '0';
        el.parentElement.style.marginLeft = '0';
      }
    }
  }

  createNewChatSession();
});
