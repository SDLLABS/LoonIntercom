import esphome.codegen as cg
from esphome.components import display, esp32
from esphome.components.esp32.const import VARIANT_ESP32S3
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_LAMBDA, CONF_PAGES

lilygo_t5_47_plus_ns = cg.esphome_ns.namespace("lilygo_t5_47_plus")
LilygoT5_47PlusDisplay = lilygo_t5_47_plus_ns.class_(
    "LilygoT5_47PlusDisplay", cg.PollingComponent, display.DisplayBuffer
)

DEPENDENCIES = ["esp32", "psram"]

CONF_PARTIAL_UPDATING = "partial_updating"
CONF_FULL_UPDATE_EVERY = "full_update_every"
CONF_MAX_PARTIAL_PERCENT = "max_partial_percent"
CONF_PARTIAL_DRIVE_PERCENT = "partial_drive_percent"

CONFIG_SCHEMA = cv.All(
    display.FULL_DISPLAY_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(LilygoT5_47PlusDisplay),
            # Klingelbox: redraw only the changed bands instead of flashing the whole screen
            cv.Optional(CONF_PARTIAL_UPDATING, default=True): cv.boolean,
            # every N partial refreshes, do one full flashing refresh to clear ghosting (0 = never)
            cv.Optional(CONF_FULL_UPDATE_EVERY, default=30): cv.int_range(min=0, max=10000),
            # above this share of changed pixels, refresh fully instead (100 = never)
            cv.Optional(CONF_MAX_PARTIAL_PERCENT, default=50): cv.int_range(min=1, max=100),
            # ink time of a partial refresh, in % of a full refresh. Keep 100: a page change undraws the
            # old page with full-refresh timing, so anything drawn with shorter frames gets more white
            # ink than it had black ink (60 % left light ghosts of a drawing, and is not DC-balanced)
            cv.Optional(CONF_PARTIAL_DRIVE_PERCENT, default=100): cv.int_range(min=10, max=150),
        }
    ).extend(cv.polling_component_schema("5s")),
    cv.has_at_most_one_key(CONF_PAGES, CONF_LAMBDA),
    cv.only_with_arduino,
    esp32.only_on_variant(supported=[VARIANT_ESP32S3]),
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])

    await display.register_display(var, config)
    cg.add(var.set_partial_updating(config[CONF_PARTIAL_UPDATING]))
    cg.add(var.set_full_update_every(config[CONF_FULL_UPDATE_EVERY]))
    cg.add(var.set_max_partial_percent(config[CONF_MAX_PARTIAL_PERCENT]))
    cg.add(var.set_partial_drive_percent(config[CONF_PARTIAL_DRIVE_PERCENT]))

    if CONF_LAMBDA in config:
        lambda_ = await cg.process_lambda(
            config[CONF_LAMBDA], [(display.DisplayRef, "it")], return_type=cg.void
        )
        cg.add(var.set_writer(lambda_))
