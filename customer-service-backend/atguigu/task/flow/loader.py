from pathlib import Path
from typing import List, Dict
import yaml

from atguigu.domain.state import DialogueState
from atguigu.task.commands.models import StartFlowCommand
from atguigu.task.commands.processor import CommandProcessor

from atguigu.task.flow.models import FlowsList, FlowSlot, Flow
from atguigu.task.flow.steps import FlowStep, CollectSlotStep


class FlowLoader:

    def _load_slots(self, slots_data:dict) -> dict[str,FlowSlot]:
        slots = {}
        for slot_name,slot_data in slots_data.items():
            slots[slot_name] = FlowSlot(name = slot_name,**slot_data)
        return slots

    def _load_flows(self, flows_data:dict[str,dict],slots:Dict[str,FlowSlot]) -> List[Flow]:
        flows :List[Flow] = []
        for flow_id,flow_data in flows_data.items():
            flow_steps:List[FlowStep] = [FlowStep.from_dict(step_data) for step_data in flow_data.get("steps",[])]
            flow_slots = []
            for flow_step in flow_steps:
                if isinstance(flow_step,CollectSlotStep):
                    flow_slots.append(slots[flow_step.slot_name])
            flow = Flow(
                id = flow_id,
                name = flow_data.get('name'),
                description= flow_data.get('description'),
                steps=flow_steps,
                slots=slots,
            )
            flows.append(flow)
        return flows

    def loader_many(self,paths:List[str | Path]) -> FlowsList:
        flows:list[Flow] = []
        slots: Dict[str,FlowSlot] = {}
        for path in paths:
            single_flowlist = self.loader(path)
            flows.extend(single_flowlist.flows)
            slots.update(single_flowlist.slots)
        return FlowsList(slots = slots,flows = flows)

    def loader(self,path:Path) -> FlowsList:
        # print(path)
        with open(path,'r',encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # print(data)
        #处理slots
        slots_data = data.get("slots",{})
        slots:Dict[str,FlowSlot] = self._load_slots(slots_data)
        #处理flows
        flows_data = data.get("flows",{})
        flows:List[Flow] = self._load_flows(flows_data,slots)
        return FlowsList(slots = slots,flows=flows)



if __name__ == '__main__':
    flow_path1 = Path(__file__).parents[3] / 'flow_config' / 'user_flows.yml'
    flow_path2 = Path(__file__).parents[3] / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.loader_many([flow_path1, flow_path2])

    processor = CommandProcessor()
    data = StartFlowCommand(
        command="start_flow",
        flow="onboarding"
    )
    state = DialogueState(
        sender_id="u1001"
    )
    processor.run([data],state,flows_list)
    print(state)
