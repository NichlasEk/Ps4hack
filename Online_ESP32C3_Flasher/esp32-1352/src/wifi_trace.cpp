#include <Arduino.h>
#include <esp_wifi.h>
#include <esp_rom_sys.h>

extern "C" {
esp_err_t __real_esp_wifi_init(const wifi_init_config_t *config);
esp_err_t __real_coex_init(void);
void __real_esp_wifi_power_domain_on(void);
esp_err_t __real_esp_wifi_init_internal(const wifi_init_config_t *config);

esp_err_t __wrap_esp_wifi_init(const wifi_init_config_t *config) {
  esp_rom_printf("TRACE wifi_init enter core=%d heap=%u\n", xPortGetCoreID(), ESP.getFreeHeap());
  esp_err_t result = __real_esp_wifi_init(config);
  esp_rom_printf("TRACE wifi_init exit result=%d\n", result);
  return result;
}

esp_err_t __wrap_coex_init(void) {
  esp_rom_printf("TRACE coex_init enter\n");
  esp_err_t result = __real_coex_init();
  esp_rom_printf("TRACE coex_init exit result=%d\n", result);
  return result;
}

void __wrap_esp_wifi_power_domain_on(void) {
  esp_rom_printf("TRACE power_domain_on enter literal=%08x\n",
                 *reinterpret_cast<volatile uint32_t *>(0x40080558));
  __real_esp_wifi_power_domain_on();
  esp_rom_printf("TRACE power_domain_on exit\n");
}

esp_err_t __wrap_esp_wifi_init_internal(const wifi_init_config_t *config) {
  esp_rom_printf("TRACE wifi_init_internal enter\n");
  esp_err_t result = __real_esp_wifi_init_internal(config);
  esp_rom_printf("TRACE wifi_init_internal exit result=%d\n", result);
  return result;
}
}
