from usdm_model.api_base_model import ApiBaseModelWithIdNameAndLabel
from usdm_model.api_base_model import ApiBaseModelWithIdNameLabelAndDesc


def label_name(self) -> str:
    return self.label if self.label else self.name


setattr(ApiBaseModelWithIdNameAndLabel, "label_name", label_name)
setattr(ApiBaseModelWithIdNameLabelAndDesc, "label_name", label_name)
