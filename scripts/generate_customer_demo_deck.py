from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


EMU_PER_INCH = 914400
SLIDE_W = int(13.333333 * EMU_PER_INCH)
SLIDE_H = int(7.5 * EMU_PER_INCH)

OUT_DIR = Path(__file__).resolve().parents[1] / "docs"
PPTX_PATH = OUT_DIR / "customer_demo_deck.pptx"
MARKDOWN_PATH = OUT_DIR / "customer_demo_deck.md"


@dataclass(frozen=True)
class Callout:
    title: str
    body: str
    color: str = "0F766E"


@dataclass(frozen=True)
class Slide:
    section: str
    title: str
    subtitle: str = ""
    bullets: tuple[str, ...] = ()
    callouts: tuple[Callout, ...] = ()
    speaker_note: str = ""
    layout: str = "content"
    background: str = "F8FAFC"
    accent: str = "0F766E"


SLIDES: tuple[Slide, ...] = (
    Slide(
        section="Demo khách hàng",
        title="Bike Store Analytics Copilot",
        subtitle="Từ dữ liệu bán lẻ đến quyết định vận hành có bằng chứng",
        bullets=(
            "Cloud analytics warehouse trên Supabase PostgreSQL.",
            "Dashboard nghiệp vụ cho Executive, Sales, Product, Inventory, Customer, Store, Staff.",
            "Copilot tiếng Việt trả lời bằng SQL, metric source và evidence.",
        ),
        callouts=(
            Callout("Business", "KPI thống nhất cho đội vận hành", "22C55E"),
            Callout("Tech", "FastAPI + Next.js + Multi-Agent AI", "38BDF8"),
            Callout("Trust", "34/34 data quality checks passed", "F97316"),
        ),
        speaker_note="Mở đầu bằng định vị: đây không chỉ là dashboard, mà là một demo end-to-end về dữ liệu, API, UI và AI có kiểm chứng.",
        layout="title",
        background="0F172A",
        accent="38BDF8",
    ),
    Slide(
        section="Bài toán",
        title="Khách hàng cần ra quyết định nhanh từ dữ liệu bán lẻ",
        subtitle="Raw CSV hoặc báo cáo rời rạc chưa đủ để điều hành doanh thu, tồn kho và cửa hàng.",
        bullets=(
            "Dữ liệu giao dịch, sản phẩm, khách hàng và tồn kho nằm rời nhau.",
            "Mỗi team dễ có một cách tính KPI khác nhau: revenue, AOV, discount, stockout.",
            "Business users cần hỏi tiếp ngay trong cuộc họp, không chờ analyst viết query thủ công.",
            "Chatbot thông thường rủi ro vì có thể trả lời không kèm nguồn dữ liệu hoặc công thức.",
        ),
        callouts=(
            Callout("Pain", "Chậm, rời rạc, khó kiểm chứng", "DC2626"),
            Callout("Goal", "Insight nhanh + có bằng chứng", "0F766E"),
        ),
        speaker_note="Đặt vấn đề theo ngôn ngữ của khách hàng: họ không mua công nghệ, họ mua tốc độ ra quyết định và niềm tin vào số liệu.",
    ),
    Slide(
        section="Giá trị nghiệp vụ",
        title="Một màn hình cho điều hành, nhiều góc nhìn cho vận hành",
        bullets=(
            "Executive overview: doanh thu, đơn hàng, khách hàng, giao trễ, nguồn mart rõ ràng.",
            "Sales: trend theo tháng/năm, AOV, discount rate và so sánh store.",
            "Product: top product, category, brand, units sold và revenue sau chiết khấu.",
            "Inventory: phát hiện stockout, stockout risk, overstock risk theo store-product.",
            "Customer: phân khúc, state/city, top customers và revenue per customer.",
        ),
        callouts=(
            Callout("Dashboard", "Câu hỏi định kỳ", "2563EB"),
            Callout("Copilot", "Câu hỏi phát sinh", "7C3AED"),
            Callout("Evidence", "SQL + metric + source table", "0F766E"),
        ),
        speaker_note="Nhấn mạnh đây là hệ thống dùng được trong buổi họp: dashboard để xem chuẩn, copilot để hỏi thêm.",
    ),
    Slide(
        section="Dữ liệu đã kiểm chứng",
        title="Baseline KPI dùng được để demo và đối chiếu",
        bullets=(
            "9 CSV không header được snapshot vào raw/ và map schema rõ ràng.",
            "1,615 orders; 4,722 order items; 1,445 customers; 321 products; 3 stores.",
            "Revenue sau chiết khấu: 7,689,116.56.",
            "Top store theo revenue: Baldwin Bikes.",
            "Late shipment rate khoảng 31.7%; data quality: 34/34 checks passed.",
        ),
        callouts=(
            Callout("Revenue", "7.69M", "16A34A"),
            Callout("Orders", "1,615", "0284C7"),
            Callout("DQ", "34/34 PASS", "EA580C"),
        ),
        speaker_note="Slide này tạo niềm tin: số liệu có baseline, không phải dashboard mock.",
    ),
    Slide(
        section="Miền nghiệp vụ",
        title="Bao phủ các câu hỏi vận hành chính của Bike Store",
        bullets=(
            "Executive: sức khỏe tổng thể và cảnh báo vận hành.",
            "Sales: revenue, orders, units sold, AOV, growth, discount.",
            "Product: product/category/brand performance, model year, selling price.",
            "Inventory: stock quantity, sales velocity, days of supply, stockout/overstock.",
            "Store, Staff, Delivery: hiệu suất cửa hàng, nhân viên và giao hàng.",
            "Data Quality: null, duplicate, foreign key, date, numeric và regression checks.",
        ),
        callouts=(
            Callout("Sales", "Doanh thu và xu hướng", "0F766E"),
            Callout("Inventory", "Rủi ro tồn kho", "F97316"),
            Callout("Customer", "Phân khúc và địa lý", "2563EB"),
        ),
        speaker_note="Đây là slide để khách hàng tự liên hệ với phòng ban của họ.",
    ),
    Slide(
        section="Demo flow",
        title="Kịch bản demo trong 8-10 phút",
        bullets=(
            "1. Login demo và mở Executive Overview.",
            "2. Show revenue 7,689,116.56, orders 1,615 và source analytics.mart_executive_summary.",
            "3. Vào Sales, filter năm 2017 để xem monthly trend, AOV và discount rate.",
            "4. Vào Products/Inventory để nối hiệu suất bán với rủi ro tồn kho.",
            "5. Vào Customers để lọc state như NY và xem segment distribution.",
            "6. Hỏi Copilot: \"Cửa hàng nào có doanh thu cao nhất?\" rồi show evidence.",
        ),
        callouts=(
            Callout("Start", "Executive Overview", "2563EB"),
            Callout("Explore", "Sales -> Product -> Inventory", "0F766E"),
            Callout("Close", "Copilot evidence block", "7C3AED"),
        ),
        speaker_note="Có thể trình bày theo đường dây: từ KPI tổng quan đến drill-down, rồi chốt bằng AI có bằng chứng.",
    ),
    Slide(
        section="AI Copilot",
        title="Copilot không chỉ là chat: mỗi câu trả lời có nguồn kiểm chứng",
        bullets=(
            "Orchestrator phân loại intent tiếng Việt và chọn domain agent phù hợp.",
            "Domain agents: Sales, Customer, Product, Inventory, Store, Staff, Data Quality.",
            "Response trả về answer, agents, SQL, rows, metrics, tables, warnings và latency.",
            "Graph RAG/metadata liên kết metric catalog, SQL templates và question examples.",
            "Khi câu hỏi chưa có template an toàn, hệ thống cảnh báo thay vì bịa số.",
        ),
        callouts=(
            Callout("Question", "Cửa hàng nào có doanh thu cao nhất?", "0F766E"),
            Callout("Route", "store_agent + sales_agent", "7C3AED"),
            Callout("Evidence", "SQL + source rows", "F97316"),
        ),
        speaker_note="Đây là điểm khác biệt lớn: khách hàng thấy AI nhưng vẫn audit được đường đi của insight.",
    ),
    Slide(
        section="Kiến trúc",
        title="End-to-end architecture",
        subtitle="Từ CSV snapshot đến warehouse, API, dashboard và copilot.",
        bullets=(
            "CSV raw files -> ETL/validation scripts -> Supabase PostgreSQL.",
            "raw/staging/analytics/agent/audit schemas tách trách nhiệm rõ ràng.",
            "Analytics marts phục vụ dashboard và API thay vì query raw data trực tiếp.",
            "FastAPI expose metrics và /copilot/ask; Next.js và Streamlit là hai UI layer.",
        ),
        callouts=(
            Callout("Source", "CSV snapshot", "64748B"),
            Callout("Warehouse", "Supabase PostgreSQL", "0F766E"),
            Callout("Experience", "Dashboard + Copilot", "2563EB"),
        ),
        speaker_note="Giải thích luồng dữ liệu bằng ngôn ngữ đơn giản, sau đó mới đi sâu vào các layer.",
        layout="flow",
    ),
    Slide(
        section="Data platform",
        title="Warehouse được thiết kế cho analytics và governance",
        bullets=(
            "raw: dữ liệu gần nguyên bản từ CSV, giữ row count source.",
            "staging: chuẩn hóa type, date, numeric, null và status label.",
            "analytics: dim/fact và marts như sales monthly, product performance, inventory risk.",
            "agent: agent_registry, metric_catalog, sql_templates, question_examples, rag_embeddings.",
            "audit: nền tảng để log ETL, data quality, copilot query và latency.",
        ),
        callouts=(
            Callout("Fact", "fact_sales, fact_inventory", "0284C7"),
            Callout("Mart", "Executive, Sales, Product, Inventory", "0F766E"),
            Callout("Catalog", "Metric + template metadata", "F97316"),
        ),
        speaker_note="Nói rõ vì sao không query thẳng CSV/raw: mart giúp KPI thống nhất, nhanh và dễ kiểm soát.",
    ),
    Slide(
        section="API & UI",
        title="FastAPI và Next.js tách bạch backend với trải nghiệm demo",
        bullets=(
            "FastAPI service layer riêng: /health, /metrics/* và /copilot/ask.",
            "API không phụ thuộc Streamlit runtime; dễ test, deploy và reuse.",
            "Next.js frontend có demo auth bằng signed HttpOnly cookie.",
            "Server-side API calls giúp không expose service-role key ra browser.",
            "Streamlit vẫn giữ vai trò local analytics workspace cho team data.",
        ),
        callouts=(
            Callout("FastAPI", "Metrics + Copilot contracts", "2563EB"),
            Callout("Next.js", "Customer demo frontend", "0F766E"),
            Callout("Streamlit", "Internal analyst workspace", "7C3AED"),
        ),
        speaker_note="Slide này cho stakeholder kỹ thuật thấy hệ thống có boundary rõ, không phải notebook được bọc UI.",
    ),
    Slide(
        section="AI guardrails",
        title="Governed AI: hỏi tự nhiên nhưng truy vấn có kiểm soát",
        bullets=(
            "Generated SQL chỉ được phép SELECT.",
            "Allowlist schema/view: analytics.* và một số agent.* metadata read-only.",
            "Mặc định có row limit, query timeout và warning khi empty/unsupported.",
            "Không gửi toàn bộ raw data hoặc PII không cần thiết vào prompt LLM.",
            "Nếu Gemini lỗi quota/service, fallback sang degraded response dựa trên template và catalog.",
        ),
        callouts=(
            Callout("Safety", "Read-only SQL", "DC2626"),
            Callout("Scope", "Approved marts only", "0F766E"),
            Callout("Fallback", "No hallucinated KPI", "F97316"),
        ),
        speaker_note="Đây là slide trả lời nỗi lo phổ biến của khách hàng về AI: bảo mật, kiểm soát và không bịa số.",
    ),
    Slide(
        section="Độ tin cậy",
        title="Demo có kiểm thử và backup path",
        bullets=(
            "Data quality report: 34/34 checks passed.",
            "Python unit/API/agent tests: 33 passed.",
            "Frontend typecheck và production build: PASS.",
            "Playwright E2E smoke: 6 passed trên desktop Chromium và mobile Chrome profiles.",
            "Mock FastAPI server giúp kiểm thử flow login, dashboard, sales filter và copilot khi offline Supabase.",
        ),
        callouts=(
            Callout("DQ", "34/34", "16A34A"),
            Callout("Tests", "33 pytest passed", "2563EB"),
            Callout("E2E", "6 Playwright passed", "F97316"),
        ),
        speaker_note="Dùng slide này nếu khách hàng hỏi 'làm sao biết demo không vỡ?'.",
    ),
    Slide(
        section="Triển khai",
        title="Sẵn sàng mở rộng từ MVP sang pilot thực tế",
        bullets=(
            "Next.js có thể deploy lên Vercel; FastAPI chạy cùng Vercel hoặc container Render/Railway/Fly.",
            "Supabase giữ vai trò cloud database/warehouse chính.",
            "Auth demo có thể nâng lên Supabase Auth/RLS khi có người dùng thật.",
            "Có thể thay CSV bằng POS/ERP connector, scheduled ETL và CI/CD.",
            "Các phân tích tiếp theo: margin/profit, reorder alert, cohort retention, role-based dashboards.",
        ),
        callouts=(
            Callout("MVP", "Demo nhanh với dữ liệu hiện có", "0F766E"),
            Callout("Pilot", "Kết nối dữ liệu thật", "2563EB"),
            Callout("Scale", "Auth, CI/CD, alerts", "7C3AED"),
        ),
        speaker_note="Kết nối demo với bước thương mại tiếp theo: pilot bằng dữ liệu thật của khách hàng.",
    ),
    Slide(
        section="Chốt demo",
        title="Thông điệp chính cho khách hàng",
        bullets=(
            "Một nguồn KPI thống nhất cho business và data team.",
            "Dashboard trả lời câu hỏi định kỳ; Copilot xử lý câu hỏi phát sinh bằng tiếng Việt.",
            "Mỗi insight có source, metric definition và SQL để kiểm chứng.",
            "Data quality, guardrails và E2E tests giúp demo đáng tin hơn một prototype thông thường.",
            "MVP đã đủ để thảo luận pilot với dữ liệu thật của khách hàng.",
        ),
        callouts=(
            Callout("See", "Nhìn KPI", "2563EB"),
            Callout("Ask", "Hỏi tiếp", "7C3AED"),
            Callout("Trust", "Kiểm chứng", "0F766E"),
        ),
        speaker_note="Kết thúc bằng ba động từ dễ nhớ: See, Ask, Trust.",
    ),
    Slide(
        section="Appendix",
        title="Backup commands cho người demo",
        bullets=(
            "API: python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000",
            "Frontend: cd frontend; npm.cmd run dev",
            "Health check: http://127.0.0.1:8000/health",
            "Frontend URL: http://127.0.0.1:3000",
            "Offline smoke test: cd frontend; npm.cmd run test:e2e",
        ),
        callouts=(
            Callout("API", "127.0.0.1:8000", "2563EB"),
            Callout("UI", "127.0.0.1:3000", "0F766E"),
            Callout("Backup", "Mock API E2E", "F97316"),
        ),
        speaker_note="Slide này để người trình bày giữ ở cuối deck; không nhất thiết show cho khách hàng nếu demo đang mượt.",
    ),
)


def emu(inches: float) -> int:
    return int(inches * EMU_PER_INCH)


def color(hex_color: str) -> str:
    return hex_color.replace("#", "").upper()


def xml_text(value: str) -> str:
    return escape(value, quote=False)


def solid_fill(hex_color: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{color(hex_color)}"/></a:solidFill>'


def no_fill() -> str:
    return "<a:noFill/>"


def line(hex_color: str | None = None, width: int = 12700) -> str:
    if hex_color is None:
        return "<a:ln><a:noFill/></a:ln>"
    return f'<a:ln w="{width}">{solid_fill(hex_color)}</a:ln>'


def paragraph(
    text: str,
    *,
    size: int,
    fill: str,
    bold: bool = False,
    align: str = "l",
) -> str:
    bold_attr = ' b="1"' if bold else ""
    return f"""
      <a:p>
        <a:pPr algn="{align}">
          <a:defRPr sz="{size}"{bold_attr}>
            {solid_fill(fill)}
            <a:latin typeface="Aptos"/>
            <a:cs typeface="Aptos"/>
          </a:defRPr>
        </a:pPr>
        <a:r>
          <a:rPr lang="vi-VN" sz="{size}"{bold_attr}>
            {solid_fill(fill)}
            <a:latin typeface="Aptos"/>
            <a:cs typeface="Aptos"/>
          </a:rPr>
          <a:t>{xml_text(text)}</a:t>
        </a:r>
        <a:endParaRPr lang="vi-VN" sz="{size}"/>
      </a:p>
    """


def text_box(
    shape_id: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: tuple[str, ...],
    *,
    size: int = 2200,
    fill: str = "0F172A",
    bold: bool = False,
    align: str = "l",
    box_fill: str | None = None,
    box_line: str | None = None,
    geom: str = "rect",
    margin: int = 91440,
) -> str:
    body = "\n".join(paragraph(item, size=size, fill=fill, bold=bold, align=align) for item in lines)
    fill_xml = solid_fill(box_fill) if box_fill else no_fill()
    line_xml = line(box_line)
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="{xml_text(name)}"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm>
          <a:off x="{emu(x)}" y="{emu(y)}"/>
          <a:ext cx="{emu(w)}" cy="{emu(h)}"/>
        </a:xfrm>
        <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
        {fill_xml}
        {line_xml}
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" anchor="t" lIns="{margin}" tIns="{margin}" rIns="{margin}" bIns="{margin}">
          <a:spAutoFit/>
        </a:bodyPr>
        <a:lstStyle/>
        {body}
      </p:txBody>
    </p:sp>
    """


def rect(
    shape_id: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    outline: str | None = None,
    geom: str = "rect",
) -> str:
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="{xml_text(name)}"/>
        <p:cNvSpPr/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm>
          <a:off x="{emu(x)}" y="{emu(y)}"/>
          <a:ext cx="{emu(w)}" cy="{emu(h)}"/>
        </a:xfrm>
        <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
        {solid_fill(fill)}
        {line(outline)}
      </p:spPr>
    </p:sp>
    """


def callout_shape(shape_id: int, callout: Callout, x: float, y: float, w: float, h: float) -> str:
    return text_box(
        shape_id,
        f"Callout {callout.title}",
        x,
        y,
        w,
        h,
        (callout.title, callout.body),
        size=1450,
        fill="0F172A",
        bold=False,
        box_fill="FFFFFF",
        box_line=callout.color,
        geom="roundRect",
        margin=76200,
    )


def title_slide_xml(slide: Slide) -> str:
    shapes: list[str] = []
    sid = 2
    shapes.append(rect(sid, "Accent strip", 0, 0, 13.333, 0.12, fill=slide.accent))
    sid += 1
    shapes.append(rect(sid, "Accent block", 9.8, 0.8, 2.8, 5.9, fill="134E4A", outline=None, geom="roundRect"))
    sid += 1
    shapes.append(text_box(sid, "Section", 0.65, 0.62, 4.4, 0.38, (slide.section.upper(),), size=1300, fill=slide.accent, bold=True))
    sid += 1
    shapes.append(text_box(sid, "Title", 0.65, 1.2, 8.7, 1.7, (slide.title,), size=4100, fill="FFFFFF", bold=True))
    sid += 1
    shapes.append(text_box(sid, "Subtitle", 0.7, 2.95, 7.7, 0.82, (slide.subtitle,), size=2050, fill="D9F99D"))
    sid += 1
    bullet_lines = tuple(f"• {item}" for item in slide.bullets)
    shapes.append(text_box(sid, "Bullets", 0.72, 4.05, 8.1, 1.85, bullet_lines, size=1700, fill="E2E8F0"))
    sid += 1
    for idx, c in enumerate(slide.callouts):
        shapes.append(
            text_box(
                sid,
                f"Title callout {idx + 1}",
                9.1,
                1.28 + idx * 1.45,
                3.65,
                1.02,
                (c.title, c.body),
                size=1500,
                fill="FFFFFF",
                box_fill=c.color,
                box_line=None,
                geom="roundRect",
            )
        )
        sid += 1
    shapes.append(text_box(sid, "Footer", 0.68, 6.86, 8.5, 0.25, ("Bike Store Multi-Agent Analytics Copilot",), size=950, fill="94A3B8"))
    return slide_shell(slide.background, "\n".join(shapes))


def content_slide_xml(slide: Slide, number: int) -> str:
    if slide.layout == "flow":
        return flow_slide_xml(slide, number)

    shapes: list[str] = []
    sid = 2
    shapes.append(rect(sid, "Top accent", 0, 0, 13.333, 0.08, fill=slide.accent))
    sid += 1
    shapes.append(text_box(sid, "Section", 0.62, 0.32, 3.8, 0.34, (slide.section.upper(),), size=1050, fill=slide.accent, bold=True))
    sid += 1
    shapes.append(text_box(sid, "Title", 0.6, 0.72, 8.65, 0.72, (slide.title,), size=2600, fill="0F172A", bold=True))
    sid += 1
    if slide.subtitle:
        shapes.append(text_box(sid, "Subtitle", 0.63, 1.42, 8.6, 0.5, (slide.subtitle,), size=1450, fill="475569"))
        sid += 1
        bullet_y = 2.05
        bullet_h = 4.45
    else:
        bullet_y = 1.72
        bullet_h = 4.8

    bullet_lines = tuple(f"• {item}" for item in slide.bullets)
    shapes.append(text_box(sid, "Bullets", 0.7, bullet_y, 7.45, bullet_h, bullet_lines, size=1680, fill="1E293B"))
    sid += 1

    callout_y = 1.62
    for idx, c in enumerate(slide.callouts):
        shapes.append(callout_shape(sid, c, 8.65, callout_y + idx * 1.35, 3.95, 1.04))
        sid += 1

    shapes.append(text_box(sid, "Slide number", 12.05, 6.88, 0.65, 0.22, (str(number),), size=850, fill="64748B", align="r"))
    return slide_shell(slide.background, "\n".join(shapes))


def flow_slide_xml(slide: Slide, number: int) -> str:
    shapes: list[str] = []
    sid = 2
    shapes.append(rect(sid, "Top accent", 0, 0, 13.333, 0.08, fill=slide.accent))
    sid += 1
    shapes.append(text_box(sid, "Section", 0.62, 0.32, 3.8, 0.34, (slide.section.upper(),), size=1050, fill=slide.accent, bold=True))
    sid += 1
    shapes.append(text_box(sid, "Title", 0.6, 0.72, 8.65, 0.72, (slide.title,), size=2600, fill="0F172A", bold=True))
    sid += 1
    shapes.append(text_box(sid, "Subtitle", 0.63, 1.42, 8.6, 0.5, (slide.subtitle,), size=1450, fill="475569"))
    sid += 1

    boxes = (
        ("CSV snapshot", "9 source files"),
        ("ETL + DQ", "load, clean, validate"),
        ("Supabase", "raw/staging/analytics"),
        ("Analytics marts", "curated KPI views"),
        ("FastAPI", "metrics + copilot"),
        ("Dashboards", "Next.js + Streamlit"),
        ("Multi-agent AI", "SQL + evidence"),
        ("Business users", "ask, inspect, decide"),
    )
    x_positions = (0.7, 3.85, 7.0, 10.15)
    y_positions = (2.1, 4.55)
    colors = ("475569", "0F766E", "2563EB", "F97316", "2563EB", "0F766E", "7C3AED", "0F172A")
    idx = 0
    for row, y in enumerate(y_positions):
        for col, x in enumerate(x_positions):
            title, body = boxes[idx]
            shapes.append(
                text_box(
                    sid,
                    f"Flow {idx + 1}",
                    x,
                    y,
                    2.42,
                    1.08,
                    (title, body),
                    size=1350,
                    fill="FFFFFF",
                    box_fill=colors[idx],
                    geom="roundRect",
                    margin=76200,
                )
            )
            sid += 1
            if col < len(x_positions) - 1:
                shapes.append(text_box(sid, f"Arrow {idx + 1}", x + 2.44, y + 0.34, 0.62, 0.25, ("->",), size=1500, fill="64748B", bold=True, align="c"))
                sid += 1
            idx += 1

    shapes.append(text_box(sid, "Flow note", 0.75, 6.0, 11.2, 0.55, tuple(f"• {item}" for item in slide.bullets[:2]), size=1280, fill="334155"))
    sid += 1
    shapes.append(text_box(sid, "Slide number", 12.05, 6.88, 0.65, 0.22, (str(number),), size=850, fill="64748B", align="r"))
    return slide_shell(slide.background, "\n".join(shapes))


def slide_shell(background: str, shapes_xml: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgPr>{solid_fill(background)}<a:effectLst/></p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      {shapes_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""


def content_types(slide_count: int) -> str:
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>
"""


def package_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def app_xml(slide_count: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex OpenXML Deck Generator</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>{slide_count}</Slides>
  <Notes>0</Notes>
  <HiddenSlides>0</HiddenSlides>
  <MMClips>0</MMClips>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Slides</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>{slide_count}</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="{slide_count}" baseType="lpstr">
      {''.join(f'<vt:lpstr>{xml_text(slide.title)}</vt:lpstr>' for slide in SLIDES)}
    </vt:vector>
  </TitlesOfParts>
  <Company></Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>
"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Bike Store Customer Demo Deck</dc:title>
  <dc:subject>Business and technical demo slides for Bike Store Analytics Copilot</dc:subject>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>
"""


def presentation_xml(slide_count: int) -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    {slide_ids}
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr>
      <a:defRPr lang="vi-VN"/>
    </a:defPPr>
  </p:defaultTextStyle>
</p:presentation>
"""


def presentation_rels(slide_count: int) -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    rels.extend(
        f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {' '.join(rels)}
</Relationships>
"""


def slide_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>
"""


def slide_master_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle><a:lvl1pPr algn="l"><a:defRPr sz="3200"/></a:lvl1pPr></p:titleStyle>
    <p:bodyStyle><a:lvl1pPr algn="l"><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>
    <p:otherStyle><a:lvl1pPr algn="l"><a:defRPr sz="1600"/></a:lvl1pPr></p:otherStyle>
  </p:txStyles>
</p:sldMaster>
"""


def slide_master_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"""


def slide_layout_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"""


def slide_layout_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"""


def theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Bike Store Theme">
  <a:themeElements>
    <a:clrScheme name="BikeStore">
      <a:dk1><a:srgbClr val="0F172A"/></a:dk1>
      <a:lt1><a:srgbClr val="F8FAFC"/></a:lt1>
      <a:dk2><a:srgbClr val="134E4A"/></a:dk2>
      <a:lt2><a:srgbClr val="E2E8F0"/></a:lt2>
      <a:accent1><a:srgbClr val="0F766E"/></a:accent1>
      <a:accent2><a:srgbClr val="2563EB"/></a:accent2>
      <a:accent3><a:srgbClr val="F97316"/></a:accent3>
      <a:accent4><a:srgbClr val="7C3AED"/></a:accent4>
      <a:accent5><a:srgbClr val="22C55E"/></a:accent5>
      <a:accent6><a:srgbClr val="38BDF8"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Aptos">
      <a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Aptos"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="BikeStore">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"/></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="85000"/><a:satMod val="120000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
        <a:solidFill><a:schemeClr val="phClr"><a:alpha val="50000"/></a:schemeClr></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>
"""


def write_markdown() -> None:
    lines = [
        "---",
        "marp: true",
        "theme: default",
        "paginate: true",
        "size: 16:9",
        "---",
        "",
    ]
    for idx, slide in enumerate(SLIDES):
        if idx:
            lines.extend(["", "---", ""])
        lines.append(f"# {slide.title}" if slide.layout == "title" else f"## {slide.title}")
        if slide.subtitle:
            lines.extend(["", slide.subtitle])
        lines.extend(["", f"**{slide.section}**", ""])
        lines.extend(f"- {item}" for item in slide.bullets)
        if slide.callouts:
            lines.extend(["", "**Điểm nhấn:**"])
            lines.extend(f"- **{item.title}:** {item.body}" for item in slide.callouts)
        if slide.speaker_note:
            lines.extend(["", f"<!-- Speaker note: {slide.speaker_note} -->"])
    MARKDOWN_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pptx() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(PPTX_PATH, "w", ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", content_types(len(SLIDES)))
        pptx.writestr("_rels/.rels", package_rels())
        pptx.writestr("docProps/app.xml", app_xml(len(SLIDES)))
        pptx.writestr("docProps/core.xml", core_xml())
        pptx.writestr("ppt/presentation.xml", presentation_xml(len(SLIDES)))
        pptx.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(SLIDES)))
        pptx.writestr("ppt/theme/theme1.xml", theme_xml())
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        pptx.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels())
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        pptx.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels())
        for idx, slide in enumerate(SLIDES, start=1):
            xml = title_slide_xml(slide) if slide.layout == "title" else content_slide_xml(slide, idx)
            pptx.writestr(f"ppt/slides/slide{idx}.xml", xml)
            pptx.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels())


def main() -> None:
    write_markdown()
    write_pptx()
    print(f"Wrote {MARKDOWN_PATH}")
    print(f"Wrote {PPTX_PATH}")


if __name__ == "__main__":
    main()
