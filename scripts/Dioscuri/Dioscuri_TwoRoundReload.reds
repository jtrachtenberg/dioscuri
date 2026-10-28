// Dioscuri: the two-round reload's arm clips (2026-10-28).
//
// V's arms play the Ashura's FPP set (chosen by the record's friendlyName,
// shared with the vanilla Ashura). Dioscuri's own reload clips
// (mod\dioscuri\anims\p[wm]a_dioscuri.anims: the three empty_reload variants,
// two rounds each) are added to the player entities by Dioscuri.archive.xl,
// gated on the AnimWrapper variable w_rifle_sniper_dioscuri. It is raised
// here while Dioscuri is in V's right hand and lowered when it leaves:
// Meigetsu's proven pattern (Meigetsu_AnimVar.reds). The weight is
// player-level state that survives weapon switches, so it must come down on
// holster; it is also cleared whenever any other weapon arrives, so a missed
// removal event can never leave the Ashura's reload overridden.

module Dioscuri

@wrapMethod(PlayerPuppet)
protected cb func OnItemAddedToSlot(evt: ref<ItemAddedToSlot>) -> Bool {
  let result = wrappedMethod(evt);
  if evt.GetSlotID() == t"AttachmentSlots.WeaponRight" {
    let itemRecord = TweakDBInterface.GetItemRecord(ItemID.GetTDBID(evt.GetItemID()));
    let weight: Float = 0.0;
    if IsDefined(itemRecord) && itemRecord.TagsContains(n"DioscuriWeapon") {
      weight = 1.0;
    }
    AnimationControllerComponent.SetAnimWrapperWeight(this, n"w_rifle_sniper_dioscuri", weight);
  }
  return result;
}

@wrapMethod(PlayerPuppet)
protected cb func OnItemRemovedFromSlot(evt: ref<ItemRemovedFromSlot>) -> Bool {
  let result = wrappedMethod(evt);
  if evt.GetSlotID() == t"AttachmentSlots.WeaponRight" {
    let itemRecord = TweakDBInterface.GetItemRecord(ItemID.GetTDBID(evt.GetItemID()));
    if IsDefined(itemRecord) && itemRecord.TagsContains(n"DioscuriWeapon") {
      AnimationControllerComponent.SetAnimWrapperWeight(this, n"w_rifle_sniper_dioscuri", 0.0);
    }
  }
  return result;
}
