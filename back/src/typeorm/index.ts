import { TestTable } from "./Test";
import { SessionTable } from "./Session";
import { UserTable } from "./User";
import { ScenarioTable } from "./Scenario"
import { ImageTable } from "./Image"

const entities = [UserTable, TestTable, SessionTable, ScenarioTable, ImageTable]
export {UserTable, TestTable, SessionTable, ScenarioTable, ImageTable}

export default entities