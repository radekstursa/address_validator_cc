import express from "express";
import fs from "fs";

const app = express();
app.use(express.json());

// Načtení adres
const addresses = JSON.parse(fs.readFileSync("./data/addresses.json", "utf8"));

// -----------------------------
// 1) VALIDACE ADRESY
// -----------------------------
app.post("/validate", (req, res) => {
  const { city, street, zip } = req.body;

  if (!city || !street || !zip) {
    return res.status(400).json({ valid: false, error: "Missing fields" });
  }

  const cityData = addresses[city];
  if (!cityData) {
    return res.json({ valid: false, reason: "city_not_found" });
  }

  const streets = cityData[zip];
  if (!streets) {
    return res.json({ valid: false, reason: "zip_not_found" });
  }

  const ok = streets.includes(street);

  res.json({
    valid: ok,
    reason: ok ? "ok" : "street_not_found"
  });
});

// -----------------------------
// 2) NÁVRHY ULIC
// -----------------------------
app.post("/suggest", (req, res) => {
  const { city, zip } = req.body;

  if (!city || !zip) {
    return res.status(400).json({ error: "Missing fields" });
  }

  const cityData = addresses[city];
  if (!cityData) {
    return res.json({ suggestions: [] });
  }

  const streets = cityData[zip] || [];

  res.json({ suggestions: streets });
});

// -----------------------------
// Start serveru
// -----------------------------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("API běží na portu", PORT));
