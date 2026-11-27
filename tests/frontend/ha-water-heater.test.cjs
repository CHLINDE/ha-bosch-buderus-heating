// Run against ha_water_heater.py's loopback Home Assistant and synthetic account.
const { chromium } = require("playwright");
const { expect } = require("playwright/test");
const assert = require("node:assert/strict");
const readline = require("node:readline");

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const language of ["de", "en"]) {
      const page = await browser.newPage({
        locale: language === "de" ? "de-DE" : "en-US",
        viewport: { width: language === "de" ? 1000 : 390, height: 1000 },
      });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      await page.addInitScript(
        ({ url, token, language }) => {
          localStorage.setItem(
            "hassTokens",
            JSON.stringify({
              hassUrl: new URL(url).origin,
              access_token: token,
              token_type: "Bearer",
              expires: Date.now() + 3600000,
              expires_in: 3600,
              clientId: new URL(url).origin + "/",
            }),
          );
          localStorage.setItem("selectedLanguage", JSON.stringify(language));
        },
        {
          url: process.env.WATER_HEATER_URL,
          token: process.env.WATER_HEATER_TOKEN,
          language,
        },
      );
      await page.goto(process.env.WATER_HEATER_URL + "test-hot-water/0");
      const tile = page.locator("hui-tile-card");
      await tile.getByText(/52/).waitFor();
      await tile.getByText(/48[,.]5/).waitFor();
      if (process.env.WATER_HEATER_SCREENSHOT && language === "de") {
        await tile.screenshot({
          path: process.env.WATER_HEATER_SCREENSHOT.replace(
            /\.png$/,
            "-tile.png",
          ),
        });
      }
      await tile.locator("ha-tile-container").click();
      const dialog = page.locator("ha-more-info-dialog");
      await dialog.waitFor({ state: "attached" });
      await page
        .locator("more-info-water_heater")
        .waitFor({ state: "attached" });
      await page
        .locator("more-info-water_heater")
        .evaluate((element) => element.updateComplete);
      await dialog
        .getByText(
          language === "de" ? "Ist-Temperatur" : "Current temperature",
          { exact: true },
        )
        .waitFor();
      const attributes = await tile.evaluate(
        (element, id) => element.hass.states[id].attributes,
        process.env.WATER_HEATER_ENTITY,
      );
      assert.equal(attributes.temperature, 52);
      assert.equal(attributes.current_temperature, 48.5);
      assert.equal(attributes.supported_features, 2);
      assert.equal(attributes.min_temp, undefined);
      if (process.env.WATER_HEATER_SCREENSHOT && language === "de") {
        await page.screenshot({ path: process.env.WATER_HEATER_SCREENSHOT });
      }
      const mode = dialog.getByRole("button", {
        name: language === "de" ? /Modus/ : /Mode/,
      });
      await mode.click();
      for (const label of language === "de"
        ? ["Aus", "Eco", "Komfort", "Auto", "Eco+"]
        : ["Off", "Eco", "Comfort", "Auto", "Eco+"]) {
        await page.getByText(label, { exact: true }).last().waitFor();
      }
      await page
        .getByText(language === "de" ? "Komfort" : "Auto", { exact: true })
        .last()
        .click();
      await expect
        .poll(() =>
          tile.evaluate(
            (element, id) => element.hass.states[id].state,
            process.env.WATER_HEATER_ENTITY,
          ),
        )
        .toBe(language === "de" ? "high" : "ownprogram");
      assert.equal(
        await tile.evaluate(
          (element, id) => element.hass.states[id].attributes.temperature,
          process.env.WATER_HEATER_ENTITY,
        ),
        null,
      );
      const input = readline.createInterface({ input: process.stdin });
      const polled = new Promise((resolve) => input.once("line", resolve));
      console.log("POLL_SIMULATED_GATEWAY");
      assert.equal(await polled, "POLL_COMPLETE");
      input.close();
      await expect
        .poll(() =>
          tile.evaluate(
            (element, id) => element.hass.states[id].attributes.temperature,
            process.env.WATER_HEATER_ENTITY,
          ),
        )
        .toBe(52);
      await page.keyboard.press("Escape");
      await mode.waitFor({ state: "hidden" });
      await tile.getByText(/52/).waitFor();
      await tile.getByText(/48[,.]5/).waitFor();
      assert.deepEqual(errors, []);
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
