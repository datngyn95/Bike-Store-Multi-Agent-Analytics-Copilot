import { Bike, KeyRound, LogIn, User } from "lucide-react";
import { redirect } from "next/navigation";

import { authConfigError, authEnabled, readSession } from "@/lib/auth";

type LoginPageProps = {
  searchParams?: Promise<{ error?: string }>;
};

const errorMessages: Record<string, string> = {
  invalid: "Thông tin đăng nhập không đúng.",
  config: "Thiếu cấu hình demo auth trong biến môi trường."
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  if (!authEnabled()) {
    redirect("/");
  }

  const session = await readSession();
  if (session) {
    redirect("/");
  }

  const params = await searchParams;
  const configError = authConfigError();
  const routeError = params?.error ? errorMessages[params.error] : null;
  const error = configError || routeError;

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="login-brand">
          <span className="brand-mark" aria-hidden="true">
            <Bike size={22} />
          </span>
          <div>
            <p className="eyebrow">Bike Store</p>
            <h1 className="page-title">Đăng nhập demo</h1>
            <p className="page-subtitle">Trợ lý phân tích</p>
          </div>
        </div>
        {error ? (
          <div className="api-notice" role="alert">
            <strong>Không thể đăng nhập</strong>
            <span>{error}</span>
          </div>
        ) : null}
        <form action="/api/auth/login" className="form-grid" method="post">
          <div className="field">
            <label htmlFor="username">Tên đăng nhập</label>
            <div className="input-icon">
              <User aria-hidden="true" />
              <input className="input" id="username" name="username" autoComplete="username" required />
            </div>
          </div>
          <div className="field">
            <label htmlFor="password">Mật khẩu</label>
            <div className="input-icon">
              <KeyRound aria-hidden="true" />
              <input
                className="input"
                id="password"
                name="password"
                autoComplete="current-password"
                required
                type="password"
              />
            </div>
          </div>
          <button className="button primary" disabled={Boolean(configError)} type="submit">
            <LogIn aria-hidden="true" />
            <span>Đăng nhập</span>
          </button>
        </form>
      </section>
    </main>
  );
}
