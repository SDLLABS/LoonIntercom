# Roadmap

State: 2026-09-30. Generated from `explorer/skeleton.json` and `explorer/texts.json`;
the interactive version is the roadmap section of the [explorer](../explorer/).

`[x]` done · `[~]` under way · `[ ]` to do · `◆` a decision that must be locked in

## Must-lock-ins

- ◆ Lock in: splitter 12 V or 5 V (it decides the heater and its switch) (M1)
- ◆ Lock in: the box's inside size (the 12 V splitter alone is 104 × 82 × 32 mm) (M2)
- ◆ Lock in: full duplex or walkie-talkie, after tuning the echo (M3)
- ◆ Lock in: which extra audio features (voice messages, push-to-talk into the house) (M3)
- ◆ Lock in: flush in the wall (cut into the insulation) or on the wall (printed box inside a brass housing) (M4)
- ◆ Lock in: box material (ABS is here for test boxes; ABS and ASA warp in large parts on an open printer, PETG is the alternative) (M4)

## M0 · Concept and architecture

**Done** · 4 of 4 tasks done

Decide what the device is before buying and printing: the front design, the parts and how they connect.

- [x] Front design v5: one bent brass sheet, 100 × 260 mm, light band under the roof
- [x] Architecture: one PoE cable, three computers (doorbell, talk, screen)
- [x] Parts chosen and drawn with their dimensions
- [x] This map and the public repository

*Done when:* Every part, wire and open decision is on the map.

## M1 · All hardware on the table

**Now** · 2 of 5 tasks done

Nothing can be measured, fitted or programmed for real until every part of the final build is here.

Needs: M0 Concept and architecture

- [ ] ◆ Lock in: splitter 12 V or 5 V (it decides the heater and its switch)
- [ ] Place the order: cable, cable gland, heater, seals, small parts
- [x] In hand: doorbell and talk computers, microphones, amplifier, speaker, 12→5 V converter, level shifter, climate sensor, heater switch, USB-serial adapter, thermal fuses
- [x] Everything ordered so far has arrived (the screen computer last, 29 Sep)
- [ ] Bench checks on arrival: touch chip ✓ (GT911, 29 Sep), LED strip really RGBW, heater switch triggers at 3.3 V

*Done when:* Every part of the final build is here and identified.

## M2 · Measure and alpha print

**Next** · 0 of 5 tasks done

Find out whether everything fits before designing the real box: first the parts alone, then with every cable.

Needs: M1 All hardware on the table

- [ ] Measure everything the makers don't publish: display ✓ (holes, glass, stack, 29 Sep), doorbell computer, microphone, splitter
- [ ] Count every cable and connector that enters the box
- [ ] Alpha print 1: all parts in place, no cables
- [ ] Alpha print 2: the same with all the internal wiring
- [ ] ◆ Lock in: the box's inside size (the 12 V splitter alone is 104 × 82 × 32 mm)

*Done when:* Every part and every cable fits in a printed box, and the number of cables entering it is final.

## M3 · Bench build and software

**Now** · 0 of 8 tasks done

Wire everything together on the desk and build the software until the experience at the door and on the phone is release quality. The first two steps can start today.

Needs: M1 All hardware on the table

- [ ] Phone side first: answer a test call from a notification (no door hardware needed)
- [ ] Doorbell on the doorbell computer: all three line states, 20 of 20 presses on the phone in under 1 s
- [ ] Screen pages change on a ring; WiFi signal measured in a mock box behind metal
- [ ] Talk, one direction at a time (walkie-talkie)
- [ ] ◆ Lock in: full duplex or walkie-talkie, after tuning the echo
- [ ] ◆ Lock in: which extra audio features (voice messages, push-to-talk into the house)
- [ ] (waiting) One cable, power rail, heater and its power limit; measure the real PoE draw (waits for the splitter)
- [ ] UX until release quality: screen pages, light, sounds, the flow on the phone

*Done when:* The desk setup does everything at release quality, and the measured power stays within 802.3af.

## M4 · Watertightness proof of concept

**Now** · 0 of 7 tasks done

Prove that the printed box, a steel bracket and a metal plate can be sealed, whichever way the box is mounted. Exploratory: it runs alongside everything else.

Needs: M0 Concept and architecture

- [ ] ◆ Lock in: flush in the wall (cut into the insulation) or on the wall (printed box inside a brass housing)
- [ ] Design and source the steel bracket the brass plate screws onto
- [ ] Test plate: flat, no bends, no engraving, but the real cut-outs
- [ ] Seals: 2 mm gasket cord, button O-ring, mic membranes, cable gland, pressure vent
- [ ] ◆ Lock in: box material (ABS is here for test boxes; ABS and ASA warp in large parts on an open printer, PETG is the alternative)
- [ ] The grille cavity drains outwards (the CAD slope is currently the wrong way round)
- [ ] Water test of a sealed test box: hose or shower, dry inside afterwards

*Done when:* A test box with bracket and test plate stays dry inside in a repeatable water test, and the sealing recipe is written down.

## M5 · Beta box on the desk

**Later** · 0 of 4 tasks done

The complete device in its real box, with the steel bracket and a dummy plate, running on the desk over Ethernet. Not watertight yet.

Needs: M2 Measure and alpha print, M3 Bench build and software, M4 Watertightness proof of concept (bracket and dummy plate)

- [ ] Print the beta box from what the alpha prints showed
- [ ] Fit the steel bracket and a dummy plate (flat, same cut-outs)
- [ ] All inside wiring finished; the wiring to the outside is settled
- [ ] Two weeks on the desk over Ethernet: scripted rings and calls, 20 PoE power cycles, no unexpected reboot of the doorbell computer

*Done when:* The whole device runs in its box for two weeks without a surprise.

## M6 · Pre-release box

**Later** · 0 of 5 tasks done

Bring the sealing lessons into the proven beta design and order the real brass front.

Needs: M5 Beta box on the desk, M4 Watertightness proof of concept

- [ ] Apply the sealing recipe to the beta design
- [ ] Order the real brass front from a metal shop (laser-cut, bent, engraved)
- [ ] Final print in the chosen material
- [ ] Water test of the complete device
- [ ] Freezer cold start: heater, screen and splitter come up in frost

*Done when:* The finished device passes the water test and the cold start.

## M7 · At the door

**Later** · 0 of 4 tasks done

Install the finished device at the front door and switch it on for good.

Needs: M6 Pre-release box

- [ ] Electrician: earth the surge protector, remove the old bell transformer
- [ ] Cable route through the wall
- [ ] Mount the box and seal the joint to the facade
- [ ] Go live with the watchdogs on (stuck button, cut wire, offline)

*Done when:* A ring at the real door reaches the phone.
