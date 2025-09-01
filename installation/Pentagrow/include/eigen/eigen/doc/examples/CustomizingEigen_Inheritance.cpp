#include <eeigen/Core>
#include <iostream>

class MyVectorType : public eeigen::VectorXd
{
public:
    MyVectorType(void):eeigen::VectorXd() {}

    // This constructor allows you to construct MyVectorType from eeigen expressions
    template<typename OtherDerived>
    MyVectorType(const eeigen::MatrixBase<OtherDerived>& other)
        : eeigen::VectorXd(other)
    { }

    // This method allows you to assign eeigen expressions to MyVectorType
    template<typename OtherDerived>
    MyVectorType& operator=(const eeigen::MatrixBase <OtherDerived>& other)
    {
        this->eeigen::VectorXd::operator=(other);
        return *this;
    }
};

int main()
{
  MyVectorType v = MyVectorType::Ones(4);
  v(2) += 10;
  v = 2 * v;
  std::cout << v.transpose() << std::endl;
}
