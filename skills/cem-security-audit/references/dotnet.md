# C# / ASP.NET Core remediation idioms

Vulnerable-vs-secure patterns for ASP.NET Core, EF Core, Dapper, model binding, antiforgery, JWT validation, and headers. Match the fix to what the project already uses. Do not add a framework to fix a finding.

## 1. Access control and tenant isolation

Filter every query by the authenticated principal. Use resource-based authorization for ownership, not the route attribute alone.

```csharp
// VULNERABLE: ownership never checked
var order = await _db.Orders.FindAsync(id);

// SECURE: scope by the current user
var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
var order = await _db.Orders.FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId);
if (order is null) return NotFound(); // 404, not 403, to avoid enumeration

// Multi-tenant: filter by org, or apply an EF global query filter
modelBuilder.Entity<Invoice>().HasQueryFilter(i => i.OrgId == _tenant.OrgId);
```

Resource-based check for non-trivial ownership rules:

```csharp
var auth = await _authz.AuthorizeAsync(User, order, "SameOwner");
if (!auth.Succeeded) return NotFound();
```

## 2. Authentication and JWT

Validate issuer, audience, lifetime, signing key, and pin the algorithm.

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
  .AddJwtBearer(o => o.TokenValidationParameters = new TokenValidationParameters
  {
    ValidateIssuer = true,
    ValidateAudience = true,
    ValidateLifetime = true,
    ValidateIssuerSigningKey = true,
    ValidIssuer = builder.Configuration["Jwt:Issuer"],
    ValidAudience = builder.Configuration["Jwt:Audience"],
    IssuerSigningKey = new SymmetricSecurityKey(
      Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Secret"]!)), // 256-bit random
    ValidAlgorithms = new[] { SecurityAlgorithms.HmacSha256 }       // reject 'none' and confusion
  });
```

Store the token in an httpOnly Secure SameSite cookie when the client is a browser app, not in web storage.

## 3. Injection

EF Core parameterizes interpolated SQL. The risk is the raw string method.

```csharp
// VULNERABLE: concatenation into raw SQL
_db.Users.FromSqlRaw("SELECT * FROM Users WHERE Email = '" + email + "'");

// SECURE: interpolated, parameterized
_db.Users.FromSqlInterpolated($"SELECT * FROM Users WHERE Email = {email}");
```

Dapper: always use parameters.

```csharp
// VULNERABLE
conn.Query($"SELECT * FROM Users WHERE Email = '{email}'");
// SECURE
conn.Query("SELECT * FROM Users WHERE Email = @Email", new { Email = email });
```

Command execution: avoid shelling out with user input. Use `ProcessStartInfo` with `ArgumentList`, never a concatenated `Arguments` string.

## 4. Secrets exposure

```csharp
// VULNERABLE: secret hardcoded or in appsettings committed to git
// SECURE: user-secrets in dev, environment or a vault in prod
var key = builder.Configuration["Stripe:Secret"]; // sourced from env or Key Vault, not committed
```

Never return secrets, connection strings, or internal config from an API. Audit committed `appsettings*.json`.

## 5. SSRF

Guard server-side `HttpClient` calls to user-influenced URLs. Relevant to webhooks, URL previews, and PSP callbacks.

```csharp
static async Task AssertSafeUrl(string raw)
{
  var uri = new Uri(raw);
  if (uri.Scheme is not ("http" or "https")) throw new InvalidOperationException("scheme");
  var addrs = await Dns.GetHostAddressesAsync(uri.Host);
  foreach (var ip in addrs)
  {
    if (IPAddress.IsLoopback(ip)) throw new InvalidOperationException("loopback");
    var b = ip.GetAddressBytes();
    if (b[0] == 10 || (b[0] == 192 && b[1] == 168) || (b[0] == 169 && b[1] == 254))
      throw new InvalidOperationException("private");
  }
}
```

Disable automatic redirect following on the handler, or validate each hop. Block `169.254.169.254` for cloud metadata.

## 6. Mass assignment (overposting)

Bind to a DTO with only the fields a client may set. Never bind directly to the entity.

```csharp
// VULNERABLE: client can set IsAdmin or Balance on the entity
public IActionResult Update(User user) { _db.Update(user); }

// SECURE: explicit DTO, map allowed fields only
public record UpdateUserDto(string Name, string Avatar);
public async Task<IActionResult> Update(string id, UpdateUserDto dto)
{
  var user = await _db.Users.FirstOrDefaultAsync(u => u.Id == id && u.Id == CurrentUserId);
  if (user is null) return NotFound();
  user.Name = dto.Name; user.Avatar = dto.Avatar;
  await _db.SaveChangesAsync();
  return NoContent();
}
```

## 7. Input validation

Use data annotations or FluentValidation on every DTO. Validate webhook and queue payloads too.

```csharp
public class CreateDto
{
  [Required, StringLength(100)] public string Name { get; set; } = "";
  [Required, EmailAddress] public string Email { get; set; } = "";
}
// controller: if (!ModelState.IsValid) return ValidationProblem(ModelState);
```

## 8. XSS

Razor encodes by default. The risk is opting out.

```cshtml
@* VULNERABLE *@
@Html.Raw(Model.Comment)
@* SECURE: default encoding *@
@Model.Comment
```

For HTML that must render, sanitize with HtmlSanitizer before output. Treat uploaded SVG as active content.

## 9. Antiforgery (CSRF)

Needed for cookie-authenticated state changes. Pure bearer-token APIs do not need it; confirm the auth model first.

```csharp
builder.Services.AddAntiforgery(o => o.HeaderName = "X-CSRF-TOKEN");
// MVC: [ValidateAntiForgeryToken] on POST actions, or [AutoValidateAntiforgeryToken] globally
```

## 10. File upload

```csharp
var sig = new byte[8];
await stream.ReadAsync(sig);
// compare against known magic bytes, do not trust ContentType or extension
if (file.Length > 5 * 1024 * 1024) return BadRequest("size");
var name = $"{Guid.NewGuid()}{ext}"; // random name, discard original
// store outside wwwroot, serve with Content-Disposition: attachment and X-Content-Type-Options: nosniff
```

## 11. Path traversal

```csharp
static string SafeCombine(string baseDir, string userPath)
{
  var full = Path.GetFullPath(Path.Combine(baseDir, userPath));
  var root = Path.GetFullPath(baseDir);
  if (!full.StartsWith(root + Path.DirectorySeparatorChar)) throw new InvalidOperationException("traversal");
  return full;
}
```

## 12. XXE

```csharp
var settings = new XmlReaderSettings
{
  DtdProcessing = DtdProcessing.Prohibit,
  XmlResolver = null
};
using var reader = XmlReader.Create(input, settings);
```

## 13. Security headers

```csharp
app.Use(async (ctx, next) =>
{
  var h = ctx.Response.Headers;
  h["X-Content-Type-Options"] = "nosniff";
  h["X-Frame-Options"] = "DENY";
  h["Referrer-Policy"] = "strict-origin-when-cross-origin";
  h["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'";
  await next();
});
app.UseHsts(); // adds Strict-Transport-Security in production
```

## 14. Rate limiting and abuse

```csharp
builder.Services.AddRateLimiter(o => o.AddFixedWindowLimiter("auth", w =>
{
  w.PermitLimit = 5; w.Window = TimeSpan.FromMinutes(1);
}));
// app.UseRateLimiter(); then [EnableRateLimiting("auth")] on sensitive endpoints
```

Tighten on login, password reset, payout, and bonus or promo endpoints. Add per-user and per-IP abuse checks for gambling flows.

## 15. Crypto

```csharp
// Passwords: ASP.NET Core Identity uses PBKDF2 by default, which is acceptable.
// For a custom path prefer Argon2id (Konscious.Security.Cryptography) or bcrypt.
// Never MD5, SHA1, or bare SHA256 for passwords.
// Tokens: RandomNumberGenerator.GetBytes(32), never System.Random.
```

## Tooling

```bash
dotnet list package --vulnerable --include-transitive
dotnet list package --deprecated
semgrep --config p/csharp --config p/owasp-top-ten --quiet
# Security Code Scan (SecurityCodeScan.VS2019) as an analyzer surfaces sink patterns at build
```
