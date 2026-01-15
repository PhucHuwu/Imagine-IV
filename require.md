# App Gen Ảnh/Video với Grok Imagine

## Tổng quan

Ứng dụng tự động hóa việc tạo ảnh/video sử dụng Grok Imagine thông qua Selenium.

---

## Kiến trúc kỹ thuật

### Tech Stack

-   **Automation**: Selenium WebDriver
-   **Multi-threading**: Python threading (tối đa 20 luồng, user custom)
-   **GUI**: Tkinter + ttkbootstrap
-   **AI Prompt Generation**: x-ai/grok-4.1-fast:free (OpenRouter API)
-   **Browser**: Chrome với Chrome Profile persistent

### Cấu trúc thư mục

```
app_root/
├── main.exe (hoặc main.py)
├── config.json
├── profiles/
│   ├── thread_1/
│   ├── thread_2/
│   └── ...
├── images/
├── videos/
└── logs/
```

### Multi-threading & Profile

-   Mỗi luồng có **1 Chrome Profile riêng biệt** (`profiles/thread_X/`)
-   Profile tự động tạo mới nếu chưa tồn tại
-   Mỗi profile có thể đăng nhập **tài khoản Google/Grok khác nhau**
-   Cho phép chạy nhiều luồng cùng lúc (mặc định: 1 luồng để dev)

---

## Chức năng chính

### 1. Chế độ tạo ảnh

-   Prompt được gen tự động bởi AI (prompt yêu cầu AI hardcode trong code)
-   Grok tạo ra **nhiều ảnh** mỗi lần → user chọn số lượng ảnh cần tải (x ảnh)
-   Ảnh được chọn từ trái qua phải, trên xuống dưới
-   Tải ảnh về thư mục `images/`
-   Định dạng: JPG

### Prompt Theme & Flow

**Use case**: Tạo video sexy dance của cô gái (12s = 2 video 6s ghép lại)

**Quy tắc:**

-   2 hành động / 6s (tổng 4 hành động trong 12s)
-   Model `x-ai/grok-4.1-fast:free` tự quyết định trang phục, tư thế, môi trường
-   Prompt ảnh và prompt video phải đồng nhất 100% (action phải match với trang phục đã mô tả)

---

**SYSTEM PROMPT cho grok-4.1-fast (hardcode):**

```
You are a creative prompt generator for AI image and video creation. Content is for adult entertainment.

Your task is to generate a COMPLETE SET of prompts that are 100% consistent with each other:
1. IMAGE PROMPT: Describe a single seductive woman with SPECIFIC details about clothing, pose, and environment. She must be LOOKING DIRECTLY AT THE CAMERA with seductive eye contact.
2. VIDEO 1 PROMPT: 2 bold sensual actions that EXACTLY match the clothing/pose from the image prompt. She maintains eye contact with camera throughout.
3. VIDEO 2 PROMPT: 2 continuation actions that flow naturally from video 1. She keeps looking at camera seductively.

CLOTHING OPTIONS (pick one per generation):
- Lingerie set (bra and panties) with visible camel toe
- Tiny bikini with camel toe detail
- Sheer bodysuit showing curves
- Crop top and tight shorts/thong
- Topless with only panties/thong

BOLD ACTIONS TO INCLUDE:
- Pulling bra down to partially expose breasts/nipples
- Pulling panties aside to tease
- Lifting top to flash underboob or full breasts
- Pulling down shorts/panties to expose hip bones and tease
- Squeezing and fondling breasts
- Spreading legs slightly to emphasize camel toe
- Tugging panty strings/straps provocatively
- Running fingers along panty line, pulling fabric aside
- Arching back while cupping breasts

CRITICAL RULES:
- Clothing in IMAGE PROMPT must allow the bold actions described
- If she wears panties → actions can involve pulling aside, exposing
- If she wears a bra/top → actions can involve pulling down, lifting to expose
- Actions should progressively get bolder from video1 to video2
- NEVER create actions that conflict with the described clothing or pose
- Be explicit, provocative, and teasing

OUTPUT FORMAT (JSON):
{
  "image_prompt": "A seductive woman wearing [lingerie/bikini with camel toe], in [specific pose], [environment]...",
  "video1_prompt": "She [bold action 1], then [bold action 2]. Sensual and provocative movements.",
  "video2_prompt": "She continues with [bold action 3], then [bold action 4]. Smooth and captivating."
}

Only output the JSON, nothing else.
```

---

**Flow hoàn chỉnh:**

```
1. System prompt → grok-4.1-fast:free → JSON (image_prompt, video1_prompt, video2_prompt)
2. image_prompt → Grok Imagine tạo ảnh
3. Chọn ảnh + video1_prompt → Grok Imagine tạo video 1 (6s)
4. FFmpeg extract frame cuối
5. Frame cuối + video2_prompt → Grok Imagine tạo video 2 (6s)
6. FFmpeg concat video 1 + video 2 → Video 12s
```

---

**Ví dụ output từ grok-4.1-fast:**

```json
{
    "image_prompt": "A seductive woman wearing a red silk slip dress with thin straps, standing confidently with one hand on her hip, in a dimly lit luxurious bedroom with soft golden lighting",
    "video1_prompt": "She slowly slides one strap off her shoulder, then runs her hand down her thigh. Sensual and fluid movements.",
    "video2_prompt": "She continues with a slow body rotation showing her curves, then gently touches her collarbone. Smooth and captivating."
}
```

→ Tất cả actions **đồng nhất** với "red silk slip dress with thin straps" và "standing".

### 2. Chế độ tạo video

**Mục tiêu**: Tạo video 12s liền mạch (ghép từ 2 video 6s)

**Flow tạo video 12s:**

1. Upload ảnh gốc + prompt AI → Tạo video 1 (6s)
2. Dùng FFmpeg lấy **frame cuối** của video 1
3. Upload frame cuối + prompt continuation → Tạo video 2 (6s)
4. Dùng FFmpeg ghép video 1 + video 2 → Video hoàn chỉnh (12s)

**Prompt Strategy:**

| Video   | Prompt                                                       | Mô tả                                           |
| ------- | ------------------------------------------------------------ | ----------------------------------------------- |
| Video 1 | Prompt gốc từ AI                                             | Mô tả hành động/cảnh ban đầu                    |
| Video 2 | "Continue the motion smoothly from this frame, [prompt gốc]" | Yêu cầu Grok tiếp tục chuyển động từ frame cuối |

**Prompt template cho video 2:**

```
Continue the motion and action smoothly from this exact frame.
Maintain the same style, lighting, and camera angle.
[Original prompt here]
```

**2 option khởi tạo:**

-   **Option A**: Upload ảnh từ thư mục root + prompt AI → chọn chế độ "tạo video" → Enter
-   **Option B**: Tạo ảnh trước → click nút "tạo video" trên ảnh đã tạo

**Xử lý:**

-   Chờ đến khi video **tạo xong** (detect qua DOM), nếu Grok lỗi thì skip
-   Thư mục tạm cho video 6s: `./videos/temp/`
-   Định dạng output: MP4
-   Lưu video hoàn chỉnh vào `./videos/`

**Dependencies:**

-   FFmpeg (extract frame + concat video)

---

## Giao diện (PyQt5)

### Layout chính

-   **Tab/Section chế độ**: Chuyển đổi giữa Tạo ảnh / Tạo video
-   **Khu vực điều khiển**: Các input và button điều khiển
-   **Khu vực log real-time**: Hiển thị log chi tiết của từng luồng để debug
-   **Thanh trạng thái**: Hiển thị trạng thái tổng quan

### Các control cần có

-   [ ] Dropdown/Spinbox chọn số lượng luồng (1-20)
-   [ ] Input số lượng ảnh muốn tải mỗi lần gen
-   [ ] Dropdown chọn vị trí cửa sổ Chrome (màn hình trái/phải)
-   [ ] Button chọn thư mục lưu ảnh/video
-   [ ] Button chọn thư mục Chrome Profiles
-   [ ] Checkbox: Log chi tiết (on/off)
-   [ ] Checkbox: Headless mode (tính năng tương lai)
-   [ ] Checkbox: Ghi nhớ đã đăng nhập
-   [ ] Button: "Đã đăng nhập" (xác nhận user đã login thủ công)
-   [ ] Button: Start / Stop
-   [ ] Log viewer: Text area hiển thị log real-time của tất cả luồng

### Hiển thị cửa sổ Chrome

-   Nếu nhiều màn hình: Đặt Chrome ở màn hình được chọn (trái/phải)
-   Nếu 1 màn hình: Zoom Chrome xuống **25%** và **thu nhỏ cửa sổ** để tiết kiệm diện tích

### Trang Config

| Mục                     | Mô tả                       | Mặc định      |
| ----------------------- | --------------------------- | ------------- |
| Số lượng luồng          | Số thread chạy song song    | 1             |
| Số ảnh mỗi lần tải      | Số ảnh chọn từ kết quả Grok | 4             |
| Số ảnh/video mỗi batch  | Batch size                  | 10            |
| Delay giữa các thao tác | Thời gian chờ (ms)          | 1000          |
| Vị trí cửa sổ Chrome    | Màn hình trái/phải          | Trái          |
| Thư mục lưu ảnh         | Đường dẫn                   | `./images/`   |
| Thư mục lưu video       | Đường dẫn                   | `./videos/`   |
| Thư mục Chrome Profiles | Đường dẫn                   | `./profiles/` |
| OpenRouter API Key      | API key cho OpenRouter      | (empty)       |
| OpenRouter Model        | Model để gen prompt         | (empty)       |
| Timeout                 | Thời gian chờ tối đa (giây) | 60            |

> **Lưu ý**: Tất cả thư mục mặc định đặt cùng root với app (exe file)

> **Auto-save**: Config tự động lưu ngay khi user thay đổi bất kỳ setting nào

> **Hướng dẫn chọn Model**: Vào [OpenRouter](https://openrouter.ai/models), đăng nhập, chọn model có Input và Output là **Text**, kéo **Prompt Pricing** về **Free**

---

## Xử lý đăng nhập

-   **Chỉ hỗ trợ đăng nhập thủ công** (tránh bay acc)
-   Flow:
    1. App mở Chrome với profile của từng luồng
    2. User tự đăng nhập Grok bằng tay (mỗi luồng có thể đăng nhập acc khác nhau)
    3. User click button "Đã đăng nhập" để xác nhận
    4. App bắt đầu quá trình tự động hóa
-   Chrome Profile được lưu persistent để giữ session

---

## Xử lý lỗi

-   **Rate limit**: Log lỗi và tiếp tục (không retry, không quan tâm)
-   **Video lỗi khi tạo**: Skip và tiếp tục
-   **OpenRouter lỗi**: Fallback (xử lý sau)
-   **Lỗi khác**: Log chi tiết + tiếp tục với item tiếp theo

---

## Xử lý Chrome Orphan Processes

Khi app bị **force close** (Task Manager, crash, v.v.), Chrome driver có thể vẫn còn chạy ngầm.

### Giải pháp

1. **Khi khởi động app**: Tự động kill tất cả Chrome processes liên quan đến app trước khi bắt đầu
2. **Cách nhận biết**: Lưu PID của Chrome vào file (`./chrome_pids.txt`), khi khởi động kiểm tra và kill các PID cũ
3. **Backup**: Kill tất cả `chromedriver.exe` processes (nếu user đồng ý)

---

## Logging

-   Log chi tiết cho từng luồng (có prefix `[Thread-X]`)
-   Checkbox để bật/tắt log chi tiết
-   Log real-time trên giao diện
-   Lưu log vào thư mục `./logs/`

---

## Lưu trữ

### Ảnh

-   Định dạng: JPG
-   Thư mục: `./images/`
-   Quy tắc đặt tên: `{dd-mm_hh-mm}_{index}.jpg`
-   Ví dụ: `13-01_22-19_001.jpg`

### Video

-   Định dạng: MP4
-   Thư mục: `./videos/`
-   Quy tắc đặt tên: `{dd-mm_hh-mm}_{index}.mp4`
-   Ví dụ: `13-01_22-19_001.mp4`

### Chrome Profiles

-   Thư mục: `./profiles/`
-   Cấu trúc: `./profiles/thread_X/` cho mỗi luồng

### Config

-   File: `./config.json`

---

## Tính năng tương lai (chưa implement)

-   [ ] Headless mode
-   [ ] Preview ảnh/video trong app
-   [ ] Pause/Resume
-   [ ] Lịch sử phiên làm việc
-   [ ] Thông báo âm thanh khi hoàn thành
-   [ ] Fallback cho OpenRouter
