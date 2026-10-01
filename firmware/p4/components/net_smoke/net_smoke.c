#include "esp_eth.h"
#include "esp_eth_mac_esp.h"
#include "esp_eth_phy.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "board_support.h"
#include "net_smoke.h"

static const char *TAG = "net_smoke";
static esp_eth_handle_t s_eth;

static void on_eth(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    (void)base;
    (void)data;
    if (id == ETHERNET_EVENT_CONNECTED) {
        ESP_LOGI(TAG, "wired link up");
    } else if (id == ETHERNET_EVENT_DISCONNECTED) {
        ESP_LOGW(TAG, "wired link down");
    }
}

static void on_ip(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    (void)base;
    (void)id;
    const ip_event_got_ip_t *event = data;
    ESP_LOGI(TAG, "wired DHCP address: " IPSTR, IP2STR(&event->ip_info.ip));
}

esp_err_t net_smoke_start(void)
{
    const struct p4_ethernet_config *board_eth = &p4_board_get()->ethernet;
    esp_err_t err = esp_netif_init();
    if (err != ESP_OK) return err;
    err = esp_event_loop_create_default();
    if (err != ESP_OK) return err;

    eth_mac_config_t mac_config = ETH_MAC_DEFAULT_CONFIG();
    eth_esp32_emac_config_t emac_config = ETH_ESP32_EMAC_DEFAULT_CONFIG();
    emac_config.smi_gpio.mdc_num = board_eth->mdc_gpio;
    emac_config.smi_gpio.mdio_num = board_eth->mdio_gpio;
    emac_config.interface = EMAC_DATA_INTERFACE_RMII;
    emac_config.clock_config.rmii.clock_mode = EMAC_CLK_EXT_IN;
    emac_config.clock_config.rmii.clock_gpio = board_eth->rmii.ref_clk_input_gpio;
    emac_config.emac_dataif_gpio.rmii.crs_dv_num = board_eth->rmii.crs_dv_gpio;
    emac_config.emac_dataif_gpio.rmii.rxd0_num = board_eth->rmii.rxd0_gpio;
    emac_config.emac_dataif_gpio.rmii.rxd1_num = board_eth->rmii.rxd1_gpio;
    emac_config.emac_dataif_gpio.rmii.txd0_num = board_eth->rmii.txd0_gpio;
    emac_config.emac_dataif_gpio.rmii.txd1_num = board_eth->rmii.txd1_gpio;
    emac_config.emac_dataif_gpio.rmii.tx_en_num = board_eth->rmii.tx_en_gpio;
    esp_eth_mac_t *mac = esp_eth_mac_new_esp32(&emac_config, &mac_config);
    if (mac == NULL) return ESP_ERR_NO_MEM;

    eth_phy_config_t phy_config = ETH_PHY_DEFAULT_CONFIG();
    phy_config.phy_addr = board_eth->phy_address;
    phy_config.reset_gpio_num = board_eth->reset_gpio;
    esp_eth_phy_t *phy = esp_eth_phy_new_ip101(&phy_config);
    if (phy == NULL) {
        mac->del(mac);
        return ESP_ERR_NO_MEM;
    }
    esp_eth_config_t eth_config = ETH_DEFAULT_CONFIG(mac, phy);
    err = esp_eth_driver_install(&eth_config, &s_eth);
    if (err != ESP_OK) {
        phy->del(phy);
        mac->del(mac);
        return err;
    }

    esp_netif_config_t netif_config = ESP_NETIF_DEFAULT_ETH();
    esp_netif_t *netif = esp_netif_new(&netif_config);
    if (netif == NULL) return ESP_ERR_NO_MEM;
    void *glue = esp_eth_new_netif_glue(s_eth);
    if (glue == NULL) return ESP_ERR_NO_MEM;
    err = esp_netif_attach(netif, glue);
    if (err != ESP_OK) return err;
    err = esp_event_handler_register(ETH_EVENT, ESP_EVENT_ANY_ID, on_eth, NULL);
    if (err != ESP_OK) return err;
    err = esp_event_handler_register(IP_EVENT, IP_EVENT_ETH_GOT_IP, on_ip, NULL);
    if (err != ESP_OK) return err;
    return esp_eth_start(s_eth);
}
