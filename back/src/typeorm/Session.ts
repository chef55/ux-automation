import { ISession } from "connect-typeorm";
import { Column, DeleteDateColumn, Entity, Index, PrimaryColumn } from "typeorm";

@Entity()
export class SessionTable implements ISession{
    @Index()
    @Column('bigint')
    expiredAt=Date.now() + 86400000

    @PrimaryColumn('varchar', {length: '255'})
    id=''

    @Column('text')
    json=''

    @DeleteDateColumn()
    public destroyedAt?: Date;
}