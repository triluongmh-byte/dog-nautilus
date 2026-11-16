# Sources
* PILOT_CONTRACT.json r001 (sealed): pins, rails, board outline/mounts.
* KiCad tool card and kicadpy README (tile): author/publish workflow.
* Module card esp32-c3-supermini/BLOCK.md (tile): pin order, 5V raw VBUS trap, strapping pins IO2/IO8/IO9.
* KiCad stock symbol/footprint libraries (Connector_Generic, Device, power, Mechanical, Connector_PinHeader_2.54mm, Resistor_SMD, Capacitor_SMD, Capacitor_THT, Diode_SMD, MountingHole).
* Vishay SS14; Yageo RC_L; Samsung CL21B104KBCNNNC; Wurth WR-PHD 6130xx11121: catalogue knowledge, no live listing opened.

## Web evidence, 2026-11-16 (search-result level; no datasheet PDF was read in full)
* ESP32-C3 SuperMini: https://esp32.co.uk/esp32-c3-supermini-pinout-safe-gpios/ , https://randomnerdtutorials.com/getting-started-esp32-c3-super-mini , https://www.sudo.is/docs/esphome/boards/esp32c3supermini/ - 16 pins on 2.54 mm, LED on GPIO8 active low, BOOT on GPIO9, strapping GPIO2/8/9, ~22 x 18 mm, pinouts vary by seller. Row spacing not found. Pin order in pinout.md agrees with these.
* C1: https://www.lcsc.com/product-detail/C88853.html (Rubycon 10PX1000MEFC8X11.5, 1000 uF 10 V, D8 x L11.5). ZLH 8x16 / 10x12.5 only: https://www.lcsc.com/product-detail/C88750.html , https://octopart.com/part/rubycon/10ZLH1000MEFC10X12.5
* BUCK1: https://www.pololu.com/product/4082/specs (S13V30F5: 2.8-22 V in, ~3 A continuous, 5 V +-3 %). MP1584 module limits: https://sparks.gogo.co.nz/assets/_site_/downloads/MP1584_Buck_Module.pdf (2 A continuous, 3 A for seconds), https://ifuturetech.org/?p=59731 . Alternative D30V30F5: https://www.pololu.com/product/4892 (5-45 V in, dropout graph not read).
* CHG1 (not chosen): USB-C 2S 2 A charger https://robu.in/product/2s-8-4v-2a-18650-lithium-battery-charger-module-type-c ; 2S 3 A protection https://rajivelectronics.com/product/2s-3a-li-ion-lithium-battery-7-4v-8-4v-18650-charger-protection-board-module ; HX-2S-JH20 10 A https://shillehtek.com/blogs/shillehtek-product-manuals/hx-2s-jh20-2s-7-4v-18650-lithium-battery-protection-board-10a-with-balancer-manual
* OLED: https://www.waveshare.com/wiki/1.54inch_OLED_Module (SSD1309, default 4-wire SPI, resistor selects I2C); https://www.siliconchip.com.au/Issue/SC/2025/November/Modules%3A+Large+OLED+Panels
* Servo: https://www.mouser.com/datasheet/2/737/FS90R_V2_0_specs-1915423.pdf (stall 550 mA @ 4.8 V / 650 mA @ 6 V), https://pololu.com/product/2820 (~800 mA @ 6 V)
* BUCK1 size: https://www.pololu.com/product/4082 (0.9 x 0.9 x 0.38 in = 22.9 x 22.9 x 9.7 mm, 3.5 g, 2-4 A typical continuous depending on input), drawing https://www.pololu.com/file/0J1807/5v-step-up-step-down-voltage-regulator-s13v30f5-dimensions.pdf
* CHG1a candidate: https://sigmanortec.ro/en/lithium-2s-3s-charging-module-with-balancing-type-c-voltage-booster (USB-C boost to 8.4 V, BM balance); USB-C 2S 4 A listing with a 9.7 V output report: https://aws.robu.in/?p=2275863 ; 5 A protection board with 8.4-9 V input: https://aws.robu.in/?p=44010
