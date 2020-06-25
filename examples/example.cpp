#include <array>
#include <cmath>
#include <complex>
#include <csignal>
#include <cstdio>

// generate GDB breakpoint
// https://github.com/nemequ/portable-snippets/tree/master/debug-trap
#include "debug-trap.h"


#define ARRAY_SIZE(a)  (sizeof(a) / sizeof(*(a)))

struct Params {
    double a;
    double b;
    double c;
    double d;

    static Params next()
    {
        static const double params[] = {
            1.0, 1.5, 0.7, 1.2, 0.3, 1.1, 1.6, 0.2, 0.8, 1.4, 0.7
        };
        static int cnt = 0;

        return {
            params[cnt++ % ARRAY_SIZE(params)],
            params[cnt++ % ARRAY_SIZE(params)],
            params[cnt++ % ARRAY_SIZE(params)],
            params[cnt++ % ARRAY_SIZE(params)],
        };
    }
};

template<typename T>
void gen_data(T *data, size_t len)
{
    Params p = Params::next();
    for (int i = 0; (size_t) i < len; ++i) {
        double t = i / 100.0;
        data[i] = p.a*15 * std::sin(t) + p.b*10 * std::sin(p.c*1.7 * t + p.d*0.6);
    }
}


int main()
{
    // static arrays of different types
    int a[1024];
    double b[1024];

    // dynamic arrays (raw pointers)
    double *c = new double[1024];
    double *d = c + 256;


    gen_data(a, ARRAY_SIZE(a));
    gen_data(b, ARRAY_SIZE(b));
    gen_data(c, 1024);
    gen_data(d, 1024 - 256);

    std::printf("And...breakpoint!\n\n");
    std::printf("Now use GDB plot command to inspect data in program variables.\n");
    std::printf("For example:\n");
    std::printf("  plot a\n");
    std::printf("  plot a b@512 a@800:0:-1\n");
    psnip_trap();

    delete[] c;

    return 0;
}
