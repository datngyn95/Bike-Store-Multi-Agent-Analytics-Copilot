---
marp: true
theme: default
paginate: true
size: 16:9
---

# Bike Store Analytics Copilot

Từ dữ liệu bán lẻ đến quyết định vận hành có bằng chứng

**Demo khách hàng**

- Cloud analytics warehouse trên Supabase PostgreSQL.
- Dashboard nghiệp vụ cho Executive, Sales, Product, Inventory, Customer, Store, Staff.
- Copilot tiếng Việt trả lời bằng SQL, metric source và evidence.

**Điểm nhấn:**
- **Business:** KPI thống nhất cho đội vận hành
- **Tech:** FastAPI + Next.js + Multi-Agent AI
- **Trust:** 34/34 data quality checks passed

<!-- Speaker note: Mở đầu bằng định vị: đây không chỉ là dashboard, mà là một demo end-to-end về dữ liệu, API, UI và AI có kiểm chứng. -->

---

## Khách hàng cần ra quyết định nhanh từ dữ liệu bán lẻ

Raw CSV hoặc báo cáo rời rạc chưa đủ để điều hành doanh thu, tồn kho và cửa hàng.

**Bài toán**

- Dữ liệu giao dịch, sản phẩm, khách hàng và tồn kho nằm rời nhau.
- Mỗi team dễ có một cách tính KPI khác nhau: revenue, AOV, discount, stockout.
- Business users cần hỏi tiếp ngay trong cuộc họp, không chờ analyst viết query thủ công.
- Chatbot thông thường rủi ro vì có thể trả lời không kèm nguồn dữ liệu hoặc công thức.

**Điểm nhấn:**
- **Pain:** Chậm, rời rạc, khó kiểm chứng
- **Goal:** Insight nhanh + có bằng chứng

<!-- Speaker note: Đặt vấn đề theo ngôn ngữ của khách hàng: họ không mua công nghệ, họ mua tốc độ ra quyết định và niềm tin vào số liệu. -->

---

## Một màn hình cho điều hành, nhiều góc nhìn cho vận hành

**Giá trị nghiệp vụ**

- Executive overview: doanh thu, đơn hàng, khách hàng, giao trễ, nguồn mart rõ ràng.
- Sales: trend theo tháng/năm, AOV, discount rate và so sánh store.
- Product: top product, category, brand, units sold và revenue sau chiết khấu.
- Inventory: phát hiện stockout, stockout risk, overstock risk theo store-product.
- Customer: phân khúc, state/city, top customers và revenue per customer.

**Điểm nhấn:**
- **Dashboard:** Câu hỏi định kỳ
- **Copilot:** Câu hỏi phát sinh
- **Evidence:** SQL + metric + source table

<!-- Speaker note: Nhấn mạnh đây là hệ thống dùng được trong buổi họp: dashboard để xem chuẩn, copilot để hỏi thêm. -->

---

## Baseline KPI dùng được để demo và đối chiếu

**Dữ liệu đã kiểm chứng**

- 9 CSV không header được snapshot vào raw/ và map schema rõ ràng.
- 1,615 orders; 4,722 order items; 1,445 customers; 321 products; 3 stores.
- Revenue sau chiết khấu: 7,689,116.56.
- Top store theo revenue: Baldwin Bikes.
- Late shipment rate khoảng 31.7%; data quality: 34/34 checks passed.

**Điểm nhấn:**
- **Revenue:** 7.69M
- **Orders:** 1,615
- **DQ:** 34/34 PASS

<!-- Speaker note: Slide này tạo niềm tin: số liệu có baseline, không phải dashboard mock. -->

---

## Bao phủ các câu hỏi vận hành chính của Bike Store

**Miền nghiệp vụ**

- Executive: sức khỏe tổng thể và cảnh báo vận hành.
- Sales: revenue, orders, units sold, AOV, growth, discount.
- Product: product/category/brand performance, model year, selling price.
- Inventory: stock quantity, sales velocity, days of supply, stockout/overstock.
- Store, Staff, Delivery: hiệu suất cửa hàng, nhân viên và giao hàng.
- Data Quality: null, duplicate, foreign key, date, numeric và regression checks.

**Điểm nhấn:**
- **Sales:** Doanh thu và xu hướng
- **Inventory:** Rủi ro tồn kho
- **Customer:** Phân khúc và địa lý

<!-- Speaker note: Đây là slide để khách hàng tự liên hệ với phòng ban của họ. -->

---

## Kịch bản demo trong 8-10 phút

**Demo flow**

- 1. Login demo và mở Executive Overview.
- 2. Show revenue 7,689,116.56, orders 1,615 và source analytics.mart_executive_summary.
- 3. Vào Sales, filter năm 2017 để xem monthly trend, AOV và discount rate.
- 4. Vào Products/Inventory để nối hiệu suất bán với rủi ro tồn kho.
- 5. Vào Customers để lọc state như NY và xem segment distribution.
- 6. Hỏi Copilot: "Cửa hàng nào có doanh thu cao nhất?" rồi show evidence.

**Điểm nhấn:**
- **Start:** Executive Overview
- **Explore:** Sales -> Product -> Inventory
- **Close:** Copilot evidence block

<!-- Speaker note: Có thể trình bày theo đường dây: từ KPI tổng quan đến drill-down, rồi chốt bằng AI có bằng chứng. -->

---

## Copilot không chỉ là chat: mỗi câu trả lời có nguồn kiểm chứng

**AI Copilot**

- Orchestrator phân loại intent tiếng Việt và chọn domain agent phù hợp.
- Domain agents: Sales, Customer, Product, Inventory, Store, Staff, Data Quality.
- Response trả về answer, agents, SQL, rows, metrics, tables, warnings và latency.
- Graph RAG/metadata liên kết metric catalog, SQL templates và question examples.
- Khi câu hỏi chưa có template an toàn, hệ thống cảnh báo thay vì bịa số.

**Điểm nhấn:**
- **Question:** Cửa hàng nào có doanh thu cao nhất?
- **Route:** store_agent + sales_agent
- **Evidence:** SQL + source rows

<!-- Speaker note: Đây là điểm khác biệt lớn: khách hàng thấy AI nhưng vẫn audit được đường đi của insight. -->

---

## End-to-end architecture

Từ CSV snapshot đến warehouse, API, dashboard và copilot.

**Kiến trúc**

- CSV raw files -> ETL/validation scripts -> Supabase PostgreSQL.
- raw/staging/analytics/agent/audit schemas tách trách nhiệm rõ ràng.
- Analytics marts phục vụ dashboard và API thay vì query raw data trực tiếp.
- FastAPI expose metrics và /copilot/ask; Next.js và Streamlit là hai UI layer.

**Điểm nhấn:**
- **Source:** CSV snapshot
- **Warehouse:** Supabase PostgreSQL
- **Experience:** Dashboard + Copilot

<!-- Speaker note: Giải thích luồng dữ liệu bằng ngôn ngữ đơn giản, sau đó mới đi sâu vào các layer. -->

---

## Warehouse được thiết kế cho analytics và governance

**Data platform**

- raw: dữ liệu gần nguyên bản từ CSV, giữ row count source.
- staging: chuẩn hóa type, date, numeric, null và status label.
- analytics: dim/fact và marts như sales monthly, product performance, inventory risk.
- agent: agent_registry, metric_catalog, sql_templates, question_examples, rag_embeddings.
- audit: nền tảng để log ETL, data quality, copilot query và latency.

**Điểm nhấn:**
- **Fact:** fact_sales, fact_inventory
- **Mart:** Executive, Sales, Product, Inventory
- **Catalog:** Metric + template metadata

<!-- Speaker note: Nói rõ vì sao không query thẳng CSV/raw: mart giúp KPI thống nhất, nhanh và dễ kiểm soát. -->

---

## FastAPI và Next.js tách bạch backend với trải nghiệm demo

**API & UI**

- FastAPI service layer riêng: /health, /metrics/* và /copilot/ask.
- API không phụ thuộc Streamlit runtime; dễ test, deploy và reuse.
- Next.js frontend có demo auth bằng signed HttpOnly cookie.
- Server-side API calls giúp không expose service-role key ra browser.
- Streamlit vẫn giữ vai trò local analytics workspace cho team data.

**Điểm nhấn:**
- **FastAPI:** Metrics + Copilot contracts
- **Next.js:** Customer demo frontend
- **Streamlit:** Internal analyst workspace

<!-- Speaker note: Slide này cho stakeholder kỹ thuật thấy hệ thống có boundary rõ, không phải notebook được bọc UI. -->

---

## Governed AI: hỏi tự nhiên nhưng truy vấn có kiểm soát

**AI guardrails**

- Generated SQL chỉ được phép SELECT.
- Allowlist schema/view: analytics.* và một số agent.* metadata read-only.
- Mặc định có row limit, query timeout và warning khi empty/unsupported.
- Không gửi toàn bộ raw data hoặc PII không cần thiết vào prompt LLM.
- Nếu Gemini lỗi quota/service, fallback sang degraded response dựa trên template và catalog.

**Điểm nhấn:**
- **Safety:** Read-only SQL
- **Scope:** Approved marts only
- **Fallback:** No hallucinated KPI

<!-- Speaker note: Đây là slide trả lời nỗi lo phổ biến của khách hàng về AI: bảo mật, kiểm soát và không bịa số. -->

---

## Demo có kiểm thử và backup path

**Độ tin cậy**

- Data quality report: 34/34 checks passed.
- Python unit/API/agent tests: 33 passed.
- Frontend typecheck và production build: PASS.
- Playwright E2E smoke: 6 passed trên desktop Chromium và mobile Chrome profiles.
- Mock FastAPI server giúp kiểm thử flow login, dashboard, sales filter và copilot khi offline Supabase.

**Điểm nhấn:**
- **DQ:** 34/34
- **Tests:** 33 pytest passed
- **E2E:** 6 Playwright passed

<!-- Speaker note: Dùng slide này nếu khách hàng hỏi 'làm sao biết demo không vỡ?'. -->

---

## Sẵn sàng mở rộng từ MVP sang pilot thực tế

**Triển khai**

- Next.js có thể deploy lên Vercel; FastAPI chạy cùng Vercel hoặc container Render/Railway/Fly.
- Supabase giữ vai trò cloud database/warehouse chính.
- Auth demo có thể nâng lên Supabase Auth/RLS khi có người dùng thật.
- Có thể thay CSV bằng POS/ERP connector, scheduled ETL và CI/CD.
- Các phân tích tiếp theo: margin/profit, reorder alert, cohort retention, role-based dashboards.

**Điểm nhấn:**
- **MVP:** Demo nhanh với dữ liệu hiện có
- **Pilot:** Kết nối dữ liệu thật
- **Scale:** Auth, CI/CD, alerts

<!-- Speaker note: Kết nối demo với bước thương mại tiếp theo: pilot bằng dữ liệu thật của khách hàng. -->

---

## Thông điệp chính cho khách hàng

**Chốt demo**

- Một nguồn KPI thống nhất cho business và data team.
- Dashboard trả lời câu hỏi định kỳ; Copilot xử lý câu hỏi phát sinh bằng tiếng Việt.
- Mỗi insight có source, metric definition và SQL để kiểm chứng.
- Data quality, guardrails và E2E tests giúp demo đáng tin hơn một prototype thông thường.
- MVP đã đủ để thảo luận pilot với dữ liệu thật của khách hàng.

**Điểm nhấn:**
- **See:** Nhìn KPI
- **Ask:** Hỏi tiếp
- **Trust:** Kiểm chứng

<!-- Speaker note: Kết thúc bằng ba động từ dễ nhớ: See, Ask, Trust. -->

---

## Backup commands cho người demo

**Appendix**

- API: python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
- Frontend: cd frontend; npm.cmd run dev
- Health check: http://127.0.0.1:8000/health
- Frontend URL: http://127.0.0.1:3000
- Offline smoke test: cd frontend; npm.cmd run test:e2e

**Điểm nhấn:**
- **API:** 127.0.0.1:8000
- **UI:** 127.0.0.1:3000
- **Backup:** Mock API E2E

<!-- Speaker note: Slide này để người trình bày giữ ở cuối deck; không nhất thiết show cho khách hàng nếu demo đang mượt. -->
