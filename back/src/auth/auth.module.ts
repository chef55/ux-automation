import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserTable } from 'src/typeorm/User';
import { UserModule } from 'src/user/user.module';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { LocalStrategy } from './local.strategy';
import { SessionSerializer } from './SessionSerializer';
import { UserService } from 'src/user/user.service';
@Module({
    imports: [TypeOrmModule.forFeature([UserTable]), UserModule,PassportModule],
    controllers: [AuthController],
    providers: [{provide: 'USER_SERVICE', useClass:UserService},
        AuthService, LocalStrategy, SessionSerializer],
})
export class AuthModule {}
