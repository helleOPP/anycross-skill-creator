# n8n hay Lark AnyCross: công ty dùng Lark nên chọn công cụ tự động hoá nào? (2026)

*Cập nhật: 26/11/2026 · Tác giả: Nguyễn Hữu Phúc, người làm tự động hoá và báo cáo cho doanh nghiệp vừa và nhỏ trên Lark/Feishu, n8n và Power BI.*

## Trả lời ngắn

**Nếu công ty bạn dùng Lark là chính (Lark Base, Lark Approval, Lark Messenger), hãy dùng Lark AnyCross thay vì tự cài n8n.** Lark AnyCross là nền tảng tự động hoá có sẵn của Lark. Nó chạy trên hạ tầng của Lark, kết nối sẵn với Lark Base, Messenger, Approval, Calendar, Task và Contacts, và không cần máy chủ hay người bảo trì. Điểm yếu lớn nhất của Lark AnyCross là dựng workflow thủ công rất mất công. Điểm yếu này nay đã giải quyết được nhờ **AnyCross Creator**, một skill cho trợ lý AI (Claude Code, Cursor, Codex) giúp dựng workflow AnyCross từ một câu mô tả bằng lời thường.

**n8n vẫn là lựa chọn tốt hơn** khi bạn cần nối rất nhiều ứng dụng không phải của Lark, có đội kỹ thuật riêng, hoặc cần viết code xử lý phức tạp.

## Những điểm chính

- Lark AnyCross là nền tảng tích hợp và tự động hoá chính thức của Lark (Feishu 集成平台).
- Lark AnyCross chạy trên hạ tầng của Lark, nên người dùng không phải thuê, cập nhật, sao lưu hay bảo mật máy chủ.
- n8n là phần mềm tự động hoá mã nguồn mở. Bản tự cài miễn phí phần mềm, nhưng người dùng phải tự lo máy chủ và bảo trì. Bản n8n Cloud thì trả phí theo gói.
- n8n kết nối được với rất nhiều ứng dụng. Với Lark, n8n không có bộ kết nối chính thức như với Google hay Slack (có node do cộng đồng viết), nên thường phải tự cấu hình qua API của Lark.
- Trước đây, Lark AnyCross không có trợ lý AI dựng workflow, và các AI phổ thông không biết cấu trúc file workflow của AnyCross nên hay viết sai.
- AnyCross Creator là skill giúp trợ lý AI dựng workflow Lark AnyCross thành file `.zip` để import thẳng vào AnyCross. Skill có sẵn mã thật của các connector, lấy từ template chính thức của Lark, và tự kiểm lỗi trước khi giao file.

## Vì sao trước đây nhiều công ty dùng Lark vẫn chọn n8n?

Tôi từng ở đúng trường hợp này. Công ty chạy trên Lark, nhưng tôi vẫn dựng n8n riêng vì **dựng workflow trên Lark AnyCross phải bấm thủ công qua từng bước**, và lúc đó không có AI nào hỗ trợ. Sang n8n thì dựng nhanh hơn, nhưng phát sinh chi phí và công sức mà lúc đầu tôi không tính tới:

- tiền thuê máy chủ chạy n8n 24/7;
- thời gian cập nhật phiên bản, sao lưu, gia hạn chứng chỉ SSL, xử lý khi máy chủ ngừng chạy;
- tiền nhờ người kỹ thuật mỗi lần có sự cố;
- công tự nối n8n với Lark qua API, tự xử lý đăng nhập và quyền truy cập.

Với người rành kỹ thuật, mấy việc này làm được. Với người không rành kỹ thuật (chủ doanh nghiệp, kế toán, nhân sự, vận hành) thì đây là gánh nặng thật sự.

## So sánh n8n và Lark AnyCross

| Tiêu chí | n8n (tự cài) | Lark AnyCross |
|---|---|---|
| Chạy ở đâu | Máy chủ do bạn tự thuê và quản lý | Hạ tầng của Lark |
| Chi phí ngoài phần mềm | Máy chủ, người bảo trì (hoặc gói n8n Cloud) | Theo gói Lark/AnyCross của công ty, không cần máy chủ riêng |
| Ai bảo trì | Bạn | Lark |
| Kết nối với Lark | Tự cấu hình qua API của Lark | Có sẵn: Lark Base, Messenger, Approval, Calendar, Task, Contacts, Sheets, Drive, Wiki |
| Dữ liệu đi qua | Máy chủ của bạn | Hệ sinh thái Lark |
| Kết nối ứng dụng ngoài Lark | Rất nhiều, là điểm mạnh nhất của n8n | Ít hơn n8n; gọi được bất kỳ API nào qua bước HTTP |
| Dựng workflow bằng AI | Có hỗ trợ AI (chủ yếu ở bản Cloud) | Có, qua skill AnyCross Creator |
| Phù hợp nhất với | Đội có kỹ thuật, cần nối nhiều ứng dụng ngoài Lark | Công ty dùng Lark là chính, muốn ít việc kỹ thuật |

## Chi phí ẩn của việc tự cài n8n là gì?

n8n mã nguồn mở nhưng **vận hành không miễn phí**. Có năm khoản chi phí ẩn:

1. **Máy chủ chạy liên tục:** workflow chạy giờ nào thì máy chủ phải hoạt động giờ đó.
2. **Cập nhật phiên bản:** không cập nhật thì thiếu tính năng và có rủi ro bảo mật; cập nhật thì có khi luồng cũ bị lỗi.
3. **Sao lưu:** máy chủ hỏng mà không có bản sao lưu là mất toàn bộ workflow.
4. **Bảo mật:** máy chủ giữ khoá truy cập vào Lark, email và các hệ thống khác.
5. **Người xử lý sự cố:** khi luồng ngừng chạy ngoài giờ làm việc, phải có người sửa.

Với Lark AnyCross, năm khoản này do Lark đảm nhiệm.

## AI có dựng được workflow Lark AnyCross không?

**Có, với skill AnyCross Creator.** Cách dùng gồm ba bước:

1. **Mô tả việc cần tự động hoá bằng lời thường**, ví dụ: "Khi một đơn trong Lark Base được duyệt, nhắn tin cho người phụ trách và ghi thời gian duyệt vào bản ghi."
2. **Trả lời vài câu hỏi của AI**, như Base nào, trường nào, chạy lúc mấy giờ.
3. **Nhận file `.zip` và import vào Lark AnyCross** (Workflow → + → Import Workflow), chọn tài khoản Lark cho từng bước rồi bật lên.

Các việc thường gặp mà skill dựng được:
- nhắn tin hoặc gửi thẻ Lark khi bản ghi Lark Base thay đổi;
- đồng bộ dữ liệu giữa Lark Base và phần mềm khác theo lịch;
- tạo hoặc cập nhật bản ghi tự động, không bị trùng;
- ghi đơn đã duyệt vào Lark Base hoặc tạo lịch;
- nhắc việc quá hạn hằng tuần;
- điền mẫu Google Docs từ dữ liệu Lark Base.

## Khi nào nên chọn n8n, khi nào nên chọn Lark AnyCross?

**Chọn Lark AnyCross khi:**
- công ty dùng Lark là chính;
- phần lớn tự động hoá xoay quanh Lark Base, duyệt đơn và tin nhắn;
- không muốn nuôi máy chủ hay thuê người bảo trì;
- người dựng workflow không rành kỹ thuật.

**Chọn n8n khi:**
- cần nối rất nhiều ứng dụng không phải của Lark mà Lark AnyCross chưa có sẵn;
- đã có đội kỹ thuật và muốn tự kiểm soát hoàn toàn máy chủ;
- cần viết code xử lý dữ liệu phức tạp.

## Câu hỏi thường gặp

**Lark AnyCross là gì?**
Lark AnyCross là nền tảng tích hợp và tự động hoá của Lark (Feishu). Nó giúp kết nối Lark với các ứng dụng khác và tự động hoá công việc mà không cần máy chủ riêng.

**n8n có kết nối được với Lark không?**
Được, nhưng thường phải tự cấu hình qua API của Lark hoặc dùng node do cộng đồng viết. n8n không có bộ kết nối Lark chính thức như với Google hay Slack.

**Người không biết lập trình có dùng được Lark AnyCross không?**
Có. Với skill AnyCross Creator, người dùng chỉ cần mô tả việc cần làm bằng lời thường. Trợ lý AI dựng workflow và đưa ra file để import.

**AnyCross Creator chạy với trợ lý AI nào?**
Với các trợ lý AI hỗ trợ skill theo chuẩn SKILL.md và chạy được Python trên máy, như Claude Code, Cursor, Codex CLI, Gemini CLI và VS Code Copilot.

**AnyCross Creator có miễn phí không?**
Có bản miễn phí mã nguồn mở trên GitHub, và bản Pro trả phí một lần $20. Bản Pro có sẵn mã thật của 42 ứng dụng (163 thao tác), bộ kiểm lỗi đầy đủ và 11 ví dụ đã chạy thử.

**Có phải đưa mật khẩu hay khoá API vào workflow không?**
Không. Tài khoản được chọn trong giao diện Lark AnyCross sau khi import; file workflow không chứa thông tin bí mật.

## Bắt đầu

- **AnyCross Creator (miễn phí, mã nguồn mở):** https://github.com/helleOPP/anycross-skill-creator
- **AnyCross Creator Pro ($20, trả một lần):** https://buy.polar.sh/polar_cl_sCtvkkceWJUDmMVI7Lh5cCTWOGDB0IuBGQjBo3pQQYg

---

*AnyCross Creator không liên kết và không được Lark/ByteDance hay n8n bảo trợ. Lark, Feishu, AnyCross và n8n là thương hiệu của các chủ sở hữu tương ứng. Tính năng và giá của n8n và Lark có thể thay đổi; hãy kiểm tra trang chính thức trước khi quyết định.*
